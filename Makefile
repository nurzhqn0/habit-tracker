.PHONY: dev api web bot migrate test lint up down backup dev-up dev-down dev-logs

backup:
	sh scripts/backup.sh

api:
	cd backend && ENVIRONMENT=development uv run uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

bot:
	cd backend && ENVIRONMENT=development uv run python -m app.workers.bot.main

migrate:
	cd backend && uv run alembic upgrade head

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check app

up:
	docker compose up --build -d

down:
	docker compose down

# Dev: backend (api + bot-optional) in Docker with hot reload; run `make web` in
# another terminal for the frontend at http://localhost:3000.
dev-up:
	docker compose -f docker-compose.dev.yml up --build -d

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f
