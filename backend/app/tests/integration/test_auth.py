import time

from app.tests.integration.conftest import _ROGUE_KEY, bearer, login, make_id_token


async def test_login_creates_user_and_tokens(client):
    tokens = await login(client, telegram_id=1000)
    assert tokens["user"]["telegram_id"] == 1000
    assert tokens["user"]["username"] == "alice1000"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = await client.get("/me", headers=bearer(tokens))
    assert me.status_code == 200
    assert me.json()["first_name"] == "Alice"


async def test_forged_signature_rejected(client):
    token = make_id_token(1001, key=_ROGUE_KEY)
    response = await client.post("/auth/telegram", json={"id_token": token})
    assert response.status_code == 403


async def test_wrong_audience_rejected(client):
    token = make_id_token(1002, aud="999999999")
    response = await client.post("/auth/telegram", json={"id_token": token})
    assert response.status_code == 403


async def test_wrong_issuer_rejected(client):
    token = make_id_token(1003, iss="https://evil.example.com")
    response = await client.post("/auth/telegram", json={"id_token": token})
    assert response.status_code == 403


async def test_expired_token_rejected(client):
    now = int(time.time())
    token = make_id_token(1004, iat=now - 7200, exp=now - 3600)
    response = await client.post("/auth/telegram", json={"id_token": token})
    assert response.status_code == 403


async def test_garbage_token_rejected(client):
    response = await client.post("/auth/telegram", json={"id_token": "not-a-jwt"})
    assert response.status_code == 403


async def test_token_without_user_id_rejected(client):
    token = make_id_token(1005, id=None)
    response = await client.post("/auth/telegram", json={"id_token": token})
    assert response.status_code == 403


async def test_refresh_rotation(client):
    tokens = await login(client, 1006)
    old_refresh = tokens["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh

    # Rotation has a short grace window: a concurrent refresh from another
    # tab (or the SSR/client race) with the old token still succeeds.
    reused = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 200
    assert reused.json()["refresh_token"] != old_refresh


async def test_logout_revokes_refresh(client):
    tokens = await login(client, 1007)
    await client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    response = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 403


async def test_me_requires_auth(client):
    assert (await client.get("/me")).status_code == 401
    assert (await client.get("/me", headers={"Authorization": "Bearer bogus"})).status_code == 401


async def test_preferences_roundtrip(client):
    tokens = await login(client, 1008)
    prefs = await client.get("/me/preferences", headers=bearer(tokens))
    assert prefs.status_code == 200
    assert prefs.json()["skip_days_enabled"] is False

    updated = await client.patch(
        "/me/preferences",
        json={"skip_days_enabled": True, "timezone": "Asia/Almaty", "theme": "dark"},
        headers=bearer(tokens),
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["skip_days_enabled"] is True
    assert body["timezone"] == "Asia/Almaty"
    assert body["theme"] == "dark"


async def test_test_login_disabled_outside_test_mode(client):
    response = await client.post("/auth/test-login")
    assert response.status_code == 404
