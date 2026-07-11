CREATE DATABASE IF NOT EXISTS sentinelx;

CREATE TABLE IF NOT EXISTS sentinelx.events
(
  ts DateTime,
  host String,
  event LowCardinality(String),
  data String,
  ingest_ts DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (host, event, ts);

CREATE TABLE IF NOT EXISTS sentinelx.alerts
(
  ts DateTime,
  host String,
  rule_name String,
  severity LowCardinality(String),
  score UInt16,
  details String,
  ingest_ts DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (host, severity, ts);
-- Project version: SentinelX V1.5
