import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:3210",
  },
  webServer: [
    {
      // arch -arm64: node may run under Rosetta (x64 nvm build) while the uv venv is arm64.
      command:
        "cd ../backend && DATABASE_URL=sqlite+aiosqlite:///./data/e2e.db TEST_MODE=1 FRONTEND_ORIGIN=http://localhost:3210 arch -arm64 uv run sh -c 'alembic upgrade head && uvicorn app.main:app --port 8210'",
      url: "http://localhost:8210/health",
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command:
        "NUXT_PUBLIC_API_BASE=http://localhost:8210/api/v1 PORT=3210 node .output/server/index.mjs",
      url: "http://localhost:3210",
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
