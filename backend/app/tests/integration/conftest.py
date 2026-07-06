import time
from collections.abc import AsyncIterator

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.infrastructure.db.base import create_engine, create_session_factory
from app.infrastructure.db.tables import Base
from app.infrastructure.telegram import oidc_verifier
from app.main import create_app

TEST_CLIENT_ID = "123456789"

TEST_SETTINGS = Settings(
    environment="development",
    database_url="sqlite+aiosqlite://",
    jwt_secret="test-secret-for-integration-tests-only",
    bot_token="12345:test-bot-token",
    tg_client_id=TEST_CLIENT_ID,
    test_mode=False,
)

# One RSA keypair for the whole test session; the verifier is patched to use it.
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()

# Rogue key for forgery tests.
_ROGUE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_id_token(telegram_id: int = 1000, *, key=None, **overrides) -> str:
    """Signs a Telegram-style OIDC id_token with the test key (or a rogue one)."""
    now = int(time.time())
    claims = {
        "iss": oidc_verifier.ISSUER,
        "aud": TEST_CLIENT_ID,
        "sub": str(telegram_id),
        "iat": now,
        "exp": now + 3600,
        "id": telegram_id,
        "name": "Alice Test",
        "given_name": "Alice",
        "preferred_username": f"alice{telegram_id}",
        "picture": None,
        **overrides,
    }
    return jwt.encode(
        {k: v for k, v in claims.items() if v is not None}, key or _PRIVATE_KEY, algorithm="RS256"
    )


@pytest.fixture
async def client(monkeypatch) -> AsyncIterator[AsyncClient]:
    from app.api.routers.auth import limiter

    limiter.enabled = False  # all test requests share one client IP
    monkeypatch.setattr(oidc_verifier, "_signing_key_from_token", lambda token: _PUBLIC_KEY)

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
    response = await client.post("/auth/telegram", json={"id_token": make_id_token(telegram_id)})
    assert response.status_code == 200, response.text
    return response.json()


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
