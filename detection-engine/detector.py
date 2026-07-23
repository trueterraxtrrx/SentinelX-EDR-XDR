import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
import yaml
from psycopg.types.json import Jsonb
from redis import Redis


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinelx:sentinelx@localhost:5432/sentinelx")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EVENT_STREAM = os.getenv("EVENT_STREAM", "sentinelx.events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "detectors")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "detector-1")
RULES_PATH = Path(os.getenv("RULES_PATH", "rules/default.yml"))
CPP_RULE_MATCHER_ENV = "SENTINELX_CPP_RULE_MATCHER"
CPP_FORCE_ENV = "SENTINELX_FORCE_CPP"
CPP_HAYSTACK_THRESHOLD_BYTES = 4096


def _sigma_rule_to_internal(rule: dict[str, Any]) -> dict[str, Any] | None:
    detection = rule.get("detection")
    if not isinstance(detection, dict):
        return None
    selection = detection.get("selection")
    if not isinstance(selection, dict):
        return None
    when: dict[str, Any] = {}
    process = selection.get("Image") or selection.get("process") or selection.get("ProcessName")
    if process:
        when["process"] = str(process).split("\\")[-1]
    contains: dict[str, str] = {}
    for key, value in selection.items():
        if key.endswith("|contains"):
            contains[key.split("|", 1)[0].lower()] = str(value)
    if contains:
        field_map = {"commandline": "cmd", "image": "name"}
        when["field_contains"] = {field_map.get(k.lower(), k.lower()): v for k, v in contains.items()}
    if not when:
        return None
    return {
        "name": rule.get("title") or rule.get("name") or "Imported Sigma Rule",
        "event": "process_create",
        "when": when,
        "score": int(rule.get("level_score", 50)),
        "severity": rule.get("level", "medium"),
    }


def normalize_rules(raw_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for rule in raw_rules:
        if "when" in rule:
            normalized.append(rule)
            continue
        converted = _sigma_rule_to_internal(rule)
        if converted:
            normalized.append(converted)
    return normalized


def validate_rules(raw_rules: list[dict[str, Any]]) -> dict[str, int]:
    internal = 0
    imported = 0
    rejected = 0
    for rule in raw_rules:
        if "when" in rule:
            internal += 1
        elif _sigma_rule_to_internal(rule):
            imported += 1
        else:
            rejected += 1
    return {"internal": internal, "imported": imported, "rejected": rejected}


def summarize_rule_severity(rules: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for rule in rules:
        severity = str(rule.get("severity") or rule.get("level") or "medium").lower()
        if severity not in summary:
            severity = "medium"
        summary[severity] += 1
    return summary


def summarize_rule_events(rules: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for rule in rules:
        event = str(rule.get("event") or "unknown")
        summary[event] = summary.get(event, 0) + 1
    return summary


def load_rules() -> list[dict[str, Any]]:
    with RULES_PATH.open("r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh) or []
    if isinstance(loaded, dict):
        loaded = [loaded]
    return normalize_rules(loaded)


def utc_from_epoch(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def haystack(event: dict[str, Any]) -> str:
    return json.dumps(event.get("data", {}), ensure_ascii=False).lower()


def _cpp_rule_matcher_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return Path(__file__).resolve().parent / "cpp" / "rule_matcher" / f"sentinelx-rule-matcher{suffix}"


def _matches_rule_cpp(event: dict[str, Any], rule: dict[str, Any]) -> bool | None:
    configured = os.getenv(CPP_RULE_MATCHER_ENV)
    binary = Path(configured) if configured else _cpp_rule_matcher_path()
    if not binary.exists():
        return None
    data = event.get("data", {})
    when = rule.get("when", {})
    event_haystack = haystack(event)
    if os.getenv(CPP_FORCE_ENV) != "1" and len(event_haystack.encode("utf-8")) < CPP_HAYSTACK_THRESHOLD_BYTES:
        return None
    pairs = [
        f"{str(expected)}\x1f{str(data.get(key, ''))}"
        for key, expected in (when.get("field_equals") or {}).items()
    ]
    pairs.extend(
        f"contains:{str(expected)}\x1f{str(data.get(key, ''))}"
        for key, expected in (when.get("field_contains") or {}).items()
    )
    needles = "\x1f".join(str(item) for item in when.get("contains_any", [])) or "-"
    payload = "\n".join(
        [
            rule.get("event") or "-",
            event.get("event") or "",
            str(when.get("process") or "-"),
            str(data.get("name", "")),
            needles,
            event_haystack,
            *pairs,
        ]
    )
    try:
        completed = subprocess.run(
            [str(binary)],
            capture_output=True,
            check=True,
            input=payload,
            text=True,
            timeout=5,
        )
        return completed.stdout.strip() == "1"
    except Exception:
        return None


def matches_rule(event: dict[str, Any], rule: dict[str, Any]) -> bool:
    cpp_result = _matches_rule_cpp(event, rule)
    if cpp_result is not None:
        return cpp_result

    if rule.get("event") and rule["event"] != event.get("event"):
        return False

    data = event.get("data", {})
    when = rule.get("when", {})

    process = when.get("process")
    if process and data.get("name", "").lower() != process.lower():
        return False

    for key, expected in (when.get("field_equals") or {}).items():
        if str(data.get(key, "")).lower() != str(expected).lower():
            return False
    for key, expected in (when.get("field_contains") or {}).items():
        if str(expected).lower() not in str(data.get(key, "")).lower():
            return False

    needles = [str(item).lower() for item in when.get("contains_any", [])]
    if needles and not any(needle in haystack(event) for needle in needles):
        return False

    return True


def ensure_group(redis: Redis) -> None:
    try:
        redis.xgroup_create(EVENT_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def store_event(conn: psycopg.Connection, event: dict[str, Any]) -> int:
    ts = utc_from_epoch(int(event["ts"]))
    host = event["host"]
    data = event.get("data", {})

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO hosts(host, os, ip, last_seen)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(host) DO UPDATE SET
              last_seen = EXCLUDED.last_seen,
              os = COALESCE(NULLIF(EXCLUDED.os, 'unknown'), hosts.os),
              ip = COALESCE(NULLIF(EXCLUDED.ip, 'unknown'), hosts.ip)
            """,
            (host, data.get("os", "unknown"), data.get("ip", "unknown"), ts),
        )
        cur.execute(
            "INSERT INTO events(ts, host, event, data) VALUES (%s, %s, %s, %s) RETURNING id",
            (ts, host, event["event"], Jsonb(data)),
        )
        event_id = cur.fetchone()[0]

        if event["event"] == "process_create":
            cur.execute(
                """
                INSERT INTO process_tree(host, pid, ppid, name, cmd, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(host, pid) DO UPDATE SET
                  ppid = EXCLUDED.ppid,
                  name = EXCLUDED.name,
                  cmd = EXCLUDED.cmd,
                  last_seen = EXCLUDED.last_seen
                """,
                (
                    host,
                    data.get("pid", 0),
                    data.get("ppid"),
                    data.get("name", "unknown"),
                    data.get("cmd", ""),
                    ts,
                    ts,
                ),
            )
    return event_id


def store_alert(conn: psycopg.Connection, event: dict[str, Any], event_id: int, rule: dict[str, Any]) -> None:
    ts = utc_from_epoch(int(event["ts"]))
    score = int(rule.get("score", 0))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO alerts(ts, host, rule_name, severity, score, event_id, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ts,
                event["host"],
                rule["name"],
                rule.get("severity", "medium"),
                score,
                event_id,
                Jsonb({"event": event, "rule": rule}),
            ),
        )
        cur.execute(
            """
            UPDATE hosts
            SET risk_score = LEAST(100, risk_score + %s), last_seen = GREATEST(last_seen, %s)
            WHERE host = %s
            """,
            (score // 4, ts, event["host"]),
        )


def main() -> None:
    rules = load_rules()
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=3,
        socket_timeout=10,
    )
    ensure_group(redis)

    while True:
        try:
            with psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=3) as conn:
                messages = redis.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {EVENT_STREAM: ">"},
                    count=50,
                    block=5000,
                )
                for _, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        event = json.loads(fields["payload"])
                        event_id = store_event(conn, event)
                        for rule in rules:
                            if matches_rule(event, rule):
                                store_alert(conn, event, event_id, rule)
                        redis.xack(EVENT_STREAM, CONSUMER_GROUP, message_id)
        except Exception as exc:
            print(f"detector error: {exc}", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
# Project version: SentinelX V1.6




