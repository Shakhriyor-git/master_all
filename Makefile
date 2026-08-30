.PHONY: up down logs sh db lint fmt prod-up prod-down prod-logs prod-migrate prod-backup

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

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f api

prod-migrate:
	docker compose -f docker-compose.prod.yml exec api alembic upgrade head

prod-backup:
	bash scripts/backup.sh
