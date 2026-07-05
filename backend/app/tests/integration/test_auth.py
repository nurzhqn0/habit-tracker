import time

from app.tests.integration.conftest import bearer, login, sign_telegram_payload, telegram_payload


async def test_login_creates_user_and_tokens(client):
    tokens = await login(client, telegram_id=1000)
    assert tokens["user"]["telegram_id"] == 1000
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = await client.get("/me", headers=bearer(tokens))
    assert me.status_code == 200
    assert me.json()["first_name"] == "Alice"


async def test_forged_hash_rejected(client):
    payload = telegram_payload(1001)
    payload["hash"] = "0" * 64
    response = await client.post("/auth/telegram", json=payload)
    assert response.status_code == 403


async def test_tampered_field_rejected(client):
    payload = telegram_payload(1002)
    payload["id"] = 9999  # signed as 1002
    response = await client.post("/auth/telegram", json=payload)
    assert response.status_code == 403


async def test_stale_auth_date_rejected(client):
    payload = sign_telegram_payload(
        {"id": 1003, "first_name": "Old", "auth_date": int(time.time()) - 25 * 3600}
    )
    response = await client.post("/auth/telegram", json=payload)
    assert response.status_code == 403


async def test_refresh_rotation(client):
    tokens = await login(client, 1004)
    old_refresh = tokens["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh

    # Old refresh token is single-use.
    reused = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 403


async def test_logout_revokes_refresh(client):
    tokens = await login(client, 1005)
    await client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    response = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 403


async def test_me_requires_auth(client):
    assert (await client.get("/me")).status_code == 401
    assert (await client.get("/me", headers={"Authorization": "Bearer bogus"})).status_code == 401


async def test_preferences_roundtrip(client):
    tokens = await login(client, 1006)
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
