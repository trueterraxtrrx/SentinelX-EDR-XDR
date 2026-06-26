# SentinelX V1.0

Defensive EDR/XDR telemetry pipeline and SOC dashboard for endpoint events, alerts and process context.

## Product Overview

SentinelX is a public MVP/portfolio version of the KRYNEX Labs endpoint security product. It demonstrates endpoint event collection, queueing, rule-based detection, risk scoring, API access and a live SOC dashboard. It is not a production EDR and does not include offensive or unauthorized control functionality.

## Key Features

- C++ endpoint agent skeleton for safe telemetry simulation.
- FastAPI ingestion gateway for event batches.
- Redis Streams event queue.
- Python detection engine with YAML rules.
- React dashboard for hosts, alerts, timeline and process tree.

## Architecture

```text
Agent -> Gateway -> Redis Streams -> Detection Engine -> PostgreSQL/ClickHouse -> API -> Dashboard
```

Each service is independently runnable and API-first. Future KRYNEX Nexus integration may provide registry, tenant and audit control-plane features.

## Tech Stack

- Agent: C++17
- Gateway/API: FastAPI
- Detection: Python, YAML rules
- Data: PostgreSQL, ClickHouse, Redis
- Frontend: React, Vite, CSS
- Packaging: Docker Compose

## Screenshots

Expected screenshots live in `docs/screenshots/`:

- `dashboard.png`
- `list-view.png`
- `detail-view.png`
- `settings.png`
- `api-docs.png`

See `docs/screenshots/README.md` for capture instructions.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: <http://localhost:5173>  
API: <http://localhost:8080/docs>  
Gateway: <http://localhost:8000/docs>

## Demo Mode

Set `DEMO_MODE=true`. The dashboard shows a clear Demo Mode badge. Demo events are defensive telemetry examples and do not require real endpoint enrollment or email verification.

## Environment Variables

Use `.env.example`. Do not commit real credentials. Key variables include `DEMO_MODE`, `DATABASE_URL`, `REDIS_URL`, `EVENT_STREAM`, `API_BASE_URL`, `POSTGRES_*`.

## API Overview

- Gateway `POST /events` - receive defensive telemetry batches.
- Gateway `GET /health` - gateway health.
- API `GET /hosts` - host risk summary.
- API `GET /alerts` - recent alerts.
- API `GET /timeline` - event timeline.
- API `GET /process-tree/{host}` - process context.

## Project Structure

```text
agent/cpp/          Safe C++ telemetry agent skeleton
gateway/            FastAPI ingestion service
detection-engine/   Rule engine worker
api-backend/        SOC API
dashboard/          React dashboard
infra/              PostgreSQL and ClickHouse schemas
tests/              Smoke tests
```

## Security Scope

SentinelX is defensive-only. It is for authorized telemetry, detection and SOC review. It must not include malware, credential theft, stealth, persistence, AV bypass, exploit code, unauthorized remote control or destructive actions.

## Roadmap

- Add richer public demo event fixtures.
- Add host detail and incident queue screens.
- Add read-only hosted dashboard mode.
- Add Sigma-style rule import planning.
- Add KRYNEX Nexus product registry integration later.

## KRYNEX Ecosystem

SentinelX provides endpoint telemetry for the broader KRYNEX Labs portfolio alongside ThreatVault, LogForge, VulnScope and Nexora CRM.

## License

MIT.
