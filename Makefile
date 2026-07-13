.PHONY: dev api web bot migrate test lint up down backup dev-up dev-down dev-logs bot-restart tunnel

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

# One command, one terminal: api + bot in Docker (hot reload), frontend on the
# host via Vite for instant HMR at http://localhost:3000. Ctrl+C stops the
# frontend; `make dev-down` stops the Docker backend. Needs BOT_TOKEN in .env.
dev:
	docker compose -f docker-compose.dev.yml --profile bot up --build -d
	cd frontend && npm run dev

# Backend only (api, no bot) in Docker with hot reload — the zero-config path
# when you don't have a bot token yet. Run `make web` in another terminal.
dev-up:
	docker compose -f docker-compose.dev.yml up --build -d

dev-down:
	docker compose -f docker-compose.dev.yml --profile bot down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

# Reload the bot after editing its code (aiogram polling has no hot reload).
bot-restart:
	docker compose -f docker-compose.dev.yml restart bot

# Expose the host frontend over HTTPS for Telegram (needs `brew install cloudflared`).
# Prints a https://<random>.trycloudflare.com — put it in BotFather + FRONTEND_ORIGIN.
tunnel:
	cloudflared tunnel --url http://localhost:3000
