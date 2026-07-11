CREATE TABLE IF NOT EXISTS hosts (
  host TEXT PRIMARY KEY,
  os TEXT DEFAULT 'unknown',
  ip TEXT DEFAULT 'unknown',
  risk_score INTEGER NOT NULL DEFAULT 0,
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  host TEXT NOT NULL REFERENCES hosts(host) ON DELETE CASCADE,
  event TEXT NOT NULL,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_host_ts ON events(host, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_event_ts ON events(event, ts DESC);

CREATE TABLE IF NOT EXISTS alerts (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  host TEXT NOT NULL REFERENCES hosts(host) ON DELETE CASCADE,
  rule_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  score INTEGER NOT NULL,
  event_id BIGINT REFERENCES events(id) ON DELETE SET NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_host_ts ON alerts(host, ts DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);

CREATE TABLE IF NOT EXISTS process_tree (
  id BIGSERIAL PRIMARY KEY,
  host TEXT NOT NULL REFERENCES hosts(host) ON DELETE CASCADE,
  pid INTEGER NOT NULL,
  ppid INTEGER,
  name TEXT NOT NULL,
  cmd TEXT,
  first_seen TIMESTAMPTZ NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL,
  UNIQUE(host, pid)
);
-- Project version: SentinelX V1.5
