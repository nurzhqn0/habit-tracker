.PHONY: dev api web bot migrate test lint up down

api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

bot:
	cd backend && uv run python -m app.workers.bot.main

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
