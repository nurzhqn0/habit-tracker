# HabitFlow

A web rebuild of [Loop Habit Tracker (uHabits)](https://github.com/iSoron/uhabits) with
collaboration on top: track yes/no and measurable habits, watch your habit strength grow
with the exact uHabits scoring algorithm, and stay accountable with friends in shared rooms.
Reminders arrive as Telegram messages — mark habits done right from the chat.

## Features

- **Habits**: yes/no + measurable (at-least / at-most targets with units), flexible
  frequencies (daily, N× per week, every N days, monthly), skip days, question marks,
  per-entry notes, archive, 20-color palette, manual ordering + sorting.
- **Statistics**: habit strength score (exponential moving average, ported 1:1 from
  uHabits with golden tests), streaks, calendar heatmap, score/bar/weekday charts,
  target progress — all custom SVG, dark-theme aware.
- **Rooms**: share habit definitions with friends, link your own habits to them,
  per-room leaderboard (score / streak / completions) and activity feed.
- **Telegram**: Login Widget auth (no passwords), bot reminders per habit time +
  weekday mask in your timezone, inline ✅ Done / ⏭ Skip / 🕐 Later buttons,
  room activity notifications.
- **Data**: Loop-format CSV export/import (ZIP), Excel export.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Nuxt 4, Vue 3, Nuxt UI v4, Pinia, custom SVG charts |
| Backend | FastAPI, SQLAlchemy 2.0 (async) + SQLite (WAL), Alembic, clean architecture (domain / application / infrastructure / api) |
| Bot | aiogram 3 worker process + APScheduler |
| Auth | Telegram Login Widget (HMAC-verified) → JWT access + rotating refresh tokens |
| Deploy | Docker Compose: nginx reverse proxy + api + bot + frontend, shared SQLite volume |

## Development

Prereqs: [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
cp .env.example .env            # fill BOT_TOKEN / BOT_USERNAME for Telegram features

cd backend && uv sync && cd ..
cd frontend && npm install && cd ..

make migrate                    # create/upgrade the SQLite schema
make api                        # FastAPI on :8000
make web                        # Nuxt on :3000
make bot                        # Telegram bot worker (optional)
```

No bot configured? Set `TEST_MODE=true` for the backend and the landing page shows a
**Dev login** button instead of the Telegram widget.

Seed demo data: `cd backend && uv run python scripts/seed.py`

## Tests

```bash
make test                       # backend: 79 tests (38 golden engine tests transcribed
                                # from the uHabits test suite, engine parity at 1e-6)
cd frontend && npx playwright test   # e2e smoke: login → habit → toggles → charts → room
```

## Production

```bash
cp .env.example .env            # set JWT_SECRET (openssl rand -hex 32), BOT_TOKEN, BOT_USERNAME,
                                # FRONTEND_ORIGIN=https://your-domain
make up                         # docker compose: nginx on :80 (and :443 once TLS is configured)
```

Production guards (enforced at startup when `ENVIRONMENT=production`, the compose default):
JWT_SECRET must be ≥32 chars and not the dev default; `TEST_MODE` must be off; API docs
(`/docs`, `/openapi.json`) are disabled. Uvicorn trusts `X-Forwarded-For` from nginx so
rate limiting sees real client IPs.

**TLS**: drop `fullchain.pem` + `privkey.pem` into `nginx/certs/`, then
`cp nginx/nginx-tls.conf.example nginx/nginx.conf`, set your domain in it, and
`docker compose restart nginx`. HSTS is enabled in the TLS config.

**Backups**: `make backup` — consistent SQLite snapshot (WAL-safe) into `backups/`.

**CI**: GitHub Actions runs backend lint+tests+pip-audit, frontend build+npm audit,
and the Playwright e2e smoke on every push/PR.

The Telegram Login Widget requires your domain to be linked to the bot via
[@BotFather](https://t.me/BotFather) → `/setdomain`.

## Architecture notes

- Scores, streaks, and auto-filled entries are **derived, never persisted** — SQLite
  stores only habits and raw entries, mirroring uHabits' design. The engine lives in
  `backend/app/domain/services/` as pure functions (no IO), ported line-by-line from
  `uhabits-core` (`ScoreList.kt`, `StreakList.kt`, `EntryList.kt`).
- The bot runs as a separate process sharing the SQLite file via WAL; the API never
  performs Telegram IO — room notifications are written as activity events and tailed
  by the bot worker.
