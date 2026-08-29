.PHONY: up down logs sh db lint fmt

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

sh:
	docker compose exec api bash

db:
	docker compose exec db psql -U $${POSTGRES_USER:-brigada} -d $${POSTGRES_DB:-brigada}

lint:
	docker compose exec api ruff check app

fmt:
	docker compose exec api ruff format app
