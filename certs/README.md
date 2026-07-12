# mTLS в SentinelX

Локальный docker-compose запускает gateway по HTTP, чтобы MVP поднимался без генерации сертификатов.

Production-схема:

1. Выпустить внутренний CA.
2. Выдать server certificate для `ingestion.sentinelx.local`.
3. Выдать client certificate каждому agent с уникальным CN/SAN, например `agent:pc-01`.
4. Поставить Envoy или Nginx перед `gateway`.
5. Включить `ssl_verify_client on` / `require_client_certificate`.
6. Передавать verified identity в gateway через доверенный header, например `X-Agent-Identity`.
7. На gateway проверять, что `host` в payload соответствует client identity.

Важно: header с identity должен выставляться только reverse proxy, а внешний клиент не должен иметь возможности подделать его напрямую.
<!-- Project version: SentinelX V1.6 -->
