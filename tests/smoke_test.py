from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRedis:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def ping(self) -> bool:
        return True

    def xadd(self, stream: str, fields: dict[str, str], maxlen: int, approximate: bool) -> str:
        self.messages.append(
            {
                "stream": stream,
                "payload": fields["payload"],
                "agent_identity": fields.get("agent_identity", ""),
                "maxlen": str(maxlen),
                "approximate": str(approximate),
            }
        )
        return f"0-{len(self.messages)}"


def test_gateway_ingests_batches() -> None:
    gateway = load_module("sentinelx_gateway", ROOT / "gateway" / "app.py")
    fake_redis = FakeRedis()
    gateway.redis = fake_redis
    client = TestClient(gateway.app)

    response = client.post(
        "/events",
        headers={"X-Agent-Identity": "agent:pc-01"},
        json={
            "events": [
                {
                    "ts": 1782440000,
                    "host": "pc-01",
                    "event": "process_create",
                    "data": {"name": "powershell.exe", "cmd": "powershell.exe -enc SQBFAFgA"},
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    assert len(fake_redis.messages) == 1
    payload = json.loads(fake_redis.messages[0]["payload"])
    assert payload["host"] == "pc-01"
    assert payload["event"] == "process_create"


def test_gateway_rejects_identity_mismatch() -> None:
    gateway = load_module("sentinelx_gateway_mismatch", ROOT / "gateway" / "app.py")
    gateway.redis = FakeRedis()
    client = TestClient(gateway.app)

    response = client.post(
        "/events",
        headers={"X-Agent-Identity": "agent:pc-02"},
        json={"events": [{"ts": 1782440000, "host": "pc-01", "event": "heartbeat", "data": {}}]},
    )

    assert response.status_code == 403


def test_detection_rules_match_expected_events() -> None:
    detector = load_module("sentinelx_detector", ROOT / "detection-engine" / "detector.py")
    detector.RULES_PATH = ROOT / "detection-engine" / "rules" / "default.yml"
    rules = detector.load_rules()

    powershell_event = {
        "ts": 1782440000,
        "host": "pc-01",
        "event": "process_create",
        "data": {"name": "powershell.exe", "cmd": "powershell.exe -enc SQBFAFgA"},
    }
    matched = [rule["name"] for rule in rules if detector.matches_rule(powershell_event, rule)]
    assert "PowerShell Obfuscation" in matched

    benign_event = {
        "ts": 1782440000,
        "host": "pc-01",
        "event": "process_create",
        "data": {"name": "notepad.exe", "cmd": "notepad.exe"},
    }
    assert not [rule["name"] for rule in rules if detector.matches_rule(benign_event, rule)]


def test_api_shapes_hosts_alerts_timeline_and_process_tree() -> None:
    api = load_module("sentinelx_api", ROOT / "api-backend" / "app.py")

    def fake_rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        normalized = " ".join(query.split()).lower()
        if "from hosts" in normalized:
            return [{"host": "pc-01", "os": "Windows", "ip": "10.0.0.5", "risk_score": 80, "last_seen": "2026-06-26T00:00:00Z"}]
        if "from alerts" in normalized and "rule_name as kind" not in normalized:
            return [{"id": 1, "ts": "2026-06-26T00:00:00Z", "host": "pc-01", "rule_name": "PowerShell Obfuscation", "severity": "high", "score": 80, "status": "open", "details": {}}]
        if "from process_tree" in normalized:
            return [
                {"pid": 100, "ppid": None, "name": "explorer.exe", "cmd": "explorer.exe", "first_seen": "2026-06-26T00:00:00Z", "last_seen": "2026-06-26T00:00:00Z"},
                {"pid": 200, "ppid": 100, "name": "powershell.exe", "cmd": "powershell.exe -enc SQBFAFgA", "first_seen": "2026-06-26T00:00:00Z", "last_seen": "2026-06-26T00:00:00Z"},
            ]
        if "from events" in normalized:
            return [{"ts": "2026-06-26T00:00:00Z", "host": "pc-01", "kind": "process_create", "data": {}}]
        if "from alerts" in normalized and "rule_name as kind" in normalized:
            return [{"ts": "2026-06-26T00:00:01Z", "host": "pc-01", "kind": "PowerShell Obfuscation", "details": {}}]
        return []

    api.rows = fake_rows
    client = TestClient(api.app)

    assert client.get("/hosts").json()[0]["host"] == "pc-01"
    assert client.get("/alerts").json()[0]["rule_name"] == "PowerShell Obfuscation"
    tree = client.get("/process-tree/pc-01").json()
    assert tree["processes"][0]["children"][0]["name"] == "powershell.exe"
    timeline = client.get("/timeline").json()
    assert timeline[0]["type"] == "alert"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([os.fspath(Path(__file__).resolve())]))
# Project version: SentinelX V1.5
