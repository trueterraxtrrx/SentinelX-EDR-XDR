# SentinelX

SentinelX - учебно-практический EDR/XDR стек уровня small enterprise SOC. Проект показывает полный путь события от endpoint-агента до SOC dashboard: сбор телеметрии, прием через TLS gateway, очередь событий, rule-based detection, risk scoring, хранение и визуализация.

## Что внутри

- C++ Agent: заготовка endpoint-агента с батчингом, heartbeat, offline queue и self-check.
- Ingestion Gateway: FastAPI сервис `POST /events`, принимает события и кладет их в Redis Streams.
- Event Bus: Redis Streams как легкая замена Kafka для локального MVP.
- Detection Engine: Python worker, читает события, применяет YAML Rule DSL, считает risk score и создает alerts.
- Storage: PostgreSQL для hosts/events/alerts/process_tree, ClickHouse DDL для аналитического event lake.
- API Backend: FastAPI с методами `GET /hosts`, `GET /alerts`, `GET /process-tree/{host}`.
- Web Dashboard: React/Vite SOC-панель с hosts map, timeline, process tree, alerts feed и risk score.

## Архитектура

```text
[Agent C++]
     |
     | mTLS / HTTPS, event batching
     v
[Ingestion Gateway]
     |
     v
[Event Bus: Redis Streams]
     |
     v
[Detection Engine]
     |
     v
[Storage: PostgreSQL + ClickHouse]
     |
     v
[API Backend: FastAPI]
     |
     v
[Web Dashboard: React]
```

## Быстрый старт

Требования:

- Docker и Docker Compose
- Node.js 20+ только если dashboard запускается без Docker
- CMake/C++17 только если собирается agent локально

Запуск всего стека:

```bash
cp .env.example .env
docker compose up --build
```

Адреса:

- Dashboard: <http://localhost:5173>
- API Backend: <http://localhost:8080/docs>
- Ingestion Gateway: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- ClickHouse: <http://localhost:8123>

Отправить тестовое событие:

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "ts": 1782440000,
        "host": "pc-01",
        "event": "process_create",
        "data": {
          "pid": 4120,
          "ppid": 984,
          "name": "powershell.exe",
          "cmd": "powershell.exe -enc SQBFAFgA"
        }
      }
    ]
  }'
```

## События агента

Базовый формат:

```json
{
  "ts": 1782440000,
  "host": "pc-01",
  "event": "process_create",
  "data": {
    "name": "powershell.exe",
    "cmd": "base64 ..."
  }
}
```

Поддерживаемые типы MVP:

- `process_create`
- `file_write`
- `network_connect`
- `registry_set`
- `shell_command`
- `heartbeat`
- `tamper_check`

## Agent C++

Папка: `agent/cpp`

Текущая реализация безопасно симулирует телеметрию и демонстрирует:

- event batching
- offline queueing в JSONL
- heartbeat
- tamper self-check
- схему для mTLS клиента
- расширяемые collectors для Windows/Linux/macOS

Сборка:

```bash
cd agent/cpp
cmake -S . -B build
cmake --build build
```

Запуск:

```bash
./build/sentinelx-agent --gateway http://localhost:8000/events --host pc-01
```

Для production-сенсоров нужно заменить симулированные collectors на OS-specific источники:

- Windows: ETW, WMI, Windows Event Log, Registry APIs, Windows Filtering Platform
- Linux: procfs, auditd/eBPF, inotify/fanotify, netlink
- macOS: EndpointSecurity Framework

## Rule DSL

Правила лежат в `detection-engine/rules/default.yml`.

Пример:

```yaml
- name: PowerShell Obfuscation
  event: process_create
  when:
    process: powershell.exe
    contains_any:
      - base64
      - -enc
      - FromBase64String
  score: 80
  severity: high
```

Поддержка MVP:

- фильтр по `event`
- `process`
- `contains_any`
- `field_equals`
- `score`
- `severity`

## API

Gateway:

- `POST /events` - прием батча событий
- `GET /health` - healthcheck

API Backend:

- `GET /hosts` - список машин с risk score
- `GET /alerts` - последние алерты
- `GET /process-tree/{host}` - дерево процессов по host
- `GET /timeline` - временная лента событий и алертов

## Ключевые инженерные решения

### Mutual TLS

В `certs/README.md` описана схема сертификатов. В MVP docker-compose gateway стартует в HTTP-режиме для удобства локального запуска. Для mTLS поставьте reverse proxy вроде Nginx/Envoy перед gateway и включите проверку client certificate.

### Event batching

Агент отправляет пачки событий, чтобы снижать overhead и не терять производительность endpoint.

### Agent heartbeat

Heartbeat помогает SOC видеть живые/потерянные endpoints. Detection engine обновляет `hosts.last_seen`.

### Offline queueing

Если gateway недоступен, агент пишет события в локальный JSONL queue и отправляет их позже.

### Tamper protection

MVP self-check считает hash собственного бинаря/пути конфигурации. В production это стоит расширить:

- проверка подписи бинаря
- watchdog service
- защищенные permissions
- remote attestation
- alert при остановке агента

## Структура проекта

```text
sentinelx/
  agent/cpp/                 C++ endpoint agent skeleton
  gateway/                   ingestion gateway
  detection-engine/          stream consumer + rules
  api-backend/               SOC API
  dashboard/                 React dashboard
  infra/postgres/            schema.sql
  infra/clickhouse/          schema.sql
  certs/                     mTLS notes
  docker-compose.yml
  .env.example
```

## Безопасность

Проект не содержит offensive automation. Он предназначен для defensive monitoring, локального обучения и разработки SOC-пайплайна. Реальные collectors должны уважать privacy, retention policy и требования законодательства.

## Roadmap

- Kafka backend вместо Redis Streams для high-throughput окружений
- ClickHouse writer для дешевого хранения больших объемов telemetry
- Sigma-like rule импорт
- anomaly scoring на rolling baseline
- RBAC, tenants, audit log
- endpoint isolation workflow
- YARA/Sigma integration
- MITRE ATT&CK mapping
