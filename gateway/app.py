import json
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EVENT_STREAM = os.getenv("EVENT_STREAM", "sentinelx.events")

redis = Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="SentinelX Ingestion Gateway", version="1.5.0")


class EndpointEvent(BaseModel):
    ts: int
    host: str = Field(min_length=1, max_length=128)
    event: str = Field(min_length=1, max_length=64)
    data: dict[str, Any] = Field(default_factory=dict)


class EventBatch(BaseModel):
    events: list[EndpointEvent] = Field(min_length=1, max_length=500)


@app.get("/health")
def health() -> dict[str, str]:
    redis.ping()
    return {"status": "ok"}


@app.post("/events")
def ingest(batch: EventBatch, x_agent_identity: str | None = Header(default=None)) -> dict[str, Any]:
    stream_ids: list[str] = []
    for event in batch.events:
        if x_agent_identity and x_agent_identity not in {event.host, f"agent:{event.host}"}:
            raise HTTPException(status_code=403, detail="agent identity does not match event host")

        stream_id = redis.xadd(
            EVENT_STREAM,
            {
                "payload": json.dumps(event.model_dump(), separators=(",", ":")),
                "agent_identity": x_agent_identity or "",
            },
            maxlen=100_000,
            approximate=True,
        )
        stream_ids.append(stream_id)

    return {"accepted": len(stream_ids), "stream_ids": stream_ids}
# Project version: SentinelX V1.5
