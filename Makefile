.PHONY: up down logs agent

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

agent:
	cmake -S agent/cpp -B agent/cpp/build
	cmake --build agent/cpp/build
# Project version: SentinelX V1.2
