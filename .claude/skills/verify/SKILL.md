---
name: verify
description: Build, launch, and drive HabitFlow (FastAPI backend + Nuxt frontend) to verify changes at the real UI. Use when verifying frontend or API changes end-to-end with Playwright screenshots.
---

# Verify HabitFlow end-to-end

## Build + launch (mirrors playwright.config.ts webServer)

```bash
cd frontend && npm run build   # produces .output/

# backend (TEST_MODE=1 enables the "Dev login" button flow):
cd backend && rm -f data/verify-e2e.db && \
  ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./data/verify-e2e.db \
  TEST_MODE=1 FRONTEND_ORIGIN=http://localhost:3210 \
  uv run sh -c 'alembic upgrade head && uvicorn app.main:app --port 8210'

# frontend (built, SSR):
cd frontend && NUXT_PUBLIC_API_BASE=http://localhost:8210/api/v1 PORT=3210 node .output/server/index.mjs
```

Health checks: `curl localhost:8210/health`, `curl localhost:3210/`.

## Drive with Playwright (no install needed — reuse frontend deps)

Script outside `frontend/`? Resolve via:
```js
import { createRequire } from "node:module";
const require = createRequire("<repo>/frontend/package.json");
const { chromium } = require("@playwright/test");
```

- Login: goto `/`, click button `/Dev login/`, wait `**/app`. Access token lands in `hf_access` cookie — reuse for direct API calls (`Authorization: Bearer`).
- Fast rich seed: POST `/api/v1/import/csv` (multipart `file`) with a Loop CSV zip (one lives in `files/`), or create habits/entries via API.
- Grid selectors: `[data-testid="habit-row"]`, `[data-testid="check-cell"]`. Heatmap day cells: `button[title="YYYY-MM-DD"]`.

## Gotchas

- **Backend "today" is user-timezone based (prefs default UTC)** and can lag the local date. Never compute "today" locally in scripts — read it from `GET /habits/{id}/stats/history` (`.today`) before clicking heatmap/grid cells; future cells are `disabled`.
- Ports 8210/3210 also used by `npx playwright test` (reuseExistingServer: false) — kill yours first: `lsof -ti:8210,3210 | xargs kill`.
- Existing e2e smoke: `cd frontend && npx playwright test` (self-hosts both servers, wipe `backend/data/e2e.db` first for deterministic runs).
- Avatar 404 warnings in server logs are normal without a real bot token.
