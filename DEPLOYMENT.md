# SentinelX V1.6 Deployment Notes

This public version is prepared for local/demo hosting, not production operation.

## Build

```bash
cd dashboard
pnpm install
pnpm run build
```

## Backend

```bash
docker compose up --build gateway detection-engine api-backend
```

## Agent

```bash
cd agent/cpp
cmake -S . -B build
cmake --build build
```

## Demo Hosting

- Set `DEMO_MODE=true`.
- Set `API_BASE_URL` to the hosted API origin.
- Do not deploy real endpoint telemetry from unmanaged devices.
- Keep PostgreSQL/ClickHouse data private.

## V1.2 Roadmap Readiness

- Keep hosted dashboards read-only for public review.
- Use synthetic endpoint event fixtures only.
- Document host-detail and incident-queue gaps before private deployment.
<!-- Project version: SentinelX V1.6 -->



