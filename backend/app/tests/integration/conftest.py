import hashlib
import hmac
import time
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.infrastructure.db.base import create_engine, create_session_factory
from app.infrastructure.db.tables import Base
from app.main import create_app

TEST_BOT_TOKEN = "12345:test-bot-token"

TEST_SETTINGS = Settings(
    environment="development",
    database_url="sqlite+aiosqlite://",
    jwt_secret="test-secret-for-integration-tests-only",
    bot_token=TEST_BOT_TOKEN,
    test_mode=False,
)


def sign_telegram_payload(payload: dict, bot_token: str = TEST_BOT_TOKEN) -> dict:
    """Signs a widget payload exactly like Telegram does."""
    fields = {k: v for k, v in payload.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return payload


def telegram_payload(telegram_id: int = 1000, **overrides) -> dict:
    payload = {
        "id": telegram_id,
        "first_name": "Alice",
        "username": f"alice{telegram_id}",
        "auth_date": int(time.time()),
        **overrides,
    }
    return sign_telegram_payload(payload)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.api.routers.auth import limiter

    limiter.enabled = False  # all test requests share one client IP
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS

    engine = create_engine(TEST_SETTINGS.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c
    await engine.dispose()
    get_settings.cache_clear()


async def login(client: AsyncClient, telegram_id: int = 1000) -> dict:
    """Logs a user in; returns the token response payload."""
    response = await client.post("/auth/telegram", json=telegram_payload(telegram_id))
    assert response.status_code == 200, response.text
    return response.json()


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
