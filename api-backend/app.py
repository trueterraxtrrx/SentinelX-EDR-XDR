import json
import os
from typing import Any

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinelx:sentinelx@localhost:5432/sentinelx")

app = FastAPI(title="SentinelX API Backend", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            result = cur.fetchall()
    return [dict(row) for row in result]


@app.get("/health")
def health() -> dict[str, str]:
    rows("SELECT 1")
    return {"status": "ok"}


@app.get("/hosts")
def hosts() -> list[dict[str, Any]]:
    return rows(
        """
        SELECT host, os, ip, risk_score, last_seen
        FROM hosts
        ORDER BY risk_score DESC, last_seen DESC
        """
    )


@app.get("/alerts")
def alerts(limit: int = 50) -> list[dict[str, Any]]:
    return rows(
        """
        SELECT id, ts, host, rule_name, severity, score, status, details
        FROM alerts
        ORDER BY ts DESC
        LIMIT %s
        """,
        (min(limit, 200),),
    )


@app.get("/process-tree/{host}")
def process_tree(host: str) -> dict[str, Any]:
    processes = rows(
        """
        SELECT pid, ppid, name, cmd, first_seen, last_seen
        FROM process_tree
        WHERE host = %s
        ORDER BY COALESCE(ppid, 0), pid
        """,
        (host,),
    )
    by_pid = {proc["pid"]: {**proc, "children": []} for proc in processes}
    roots = []
    for proc in by_pid.values():
        parent = by_pid.get(proc["ppid"])
        if parent:
            parent["children"].append(proc)
        else:
            roots.append(proc)
    return {"host": host, "processes": roots}


@app.get("/timeline")
def timeline(limit: int = 100) -> list[dict[str, Any]]:
    events = rows(
        """
        SELECT ts, host, event AS kind, data
        FROM events
        ORDER BY ts DESC
        LIMIT %s
        """,
        (min(limit, 200),),
    )
    alert_rows = rows(
        """
        SELECT ts, host, rule_name AS kind, details
        FROM alerts
        ORDER BY ts DESC
        LIMIT %s
        """,
        (min(limit, 200),),
    )
    merged = [
        {"type": "event", **event}
        for event in events
    ] + [
        {"type": "alert", **alert}
        for alert in alert_rows
    ]
    return sorted(merged, key=lambda item: item["ts"], reverse=True)[: min(limit, 200)]
# Project version: SentinelX V1.2
