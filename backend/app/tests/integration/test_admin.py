from datetime import date

import pytest

from app.config import Settings

from .conftest import TEST_SETTINGS, bearer, login

# Telegram IDs 9100+ to stay clear of other test files.
ADMIN_TG_ID = 9100
OTHER_TG_ID = 9101

ADMIN_ROUTES = [
    "/admin/stats",
    "/admin/users",
    f"/admin/users/1?from={date.today()}&to={date.today()}",
    "/admin/rooms",
    "/admin/rooms/1",
]


@pytest.fixture
def admin_enabled(monkeypatch):
    # Normalized value, as the Settings validator would produce it.
    monkeypatch.setattr(TEST_SETTINGS, "admin_username", f"alice{ADMIN_TG_ID}")


def test_admin_username_setting_is_normalized():
    assert Settings(admin_username="@NurZhqn0").admin_username == "nurzhqn0"


async def test_admin_routes_require_auth(client):
    for route in ADMIN_ROUTES:
        response = await client.get(route)
        assert response.status_code == 401, route


async def test_admin_routes_forbidden_for_non_admin(client, admin_enabled):
    tokens = await login(client, OTHER_TG_ID)
    for route in ADMIN_ROUTES:
        response = await client.get(route, headers=bearer(tokens))
        assert response.status_code == 403, route


async def test_admin_routes_forbidden_when_admin_unset(client):
    assert TEST_SETTINGS.admin_username == ""
    tokens = await login(client, ADMIN_TG_ID)
    response = await client.get("/admin/stats", headers=bearer(tokens))
    assert response.status_code == 403


async def test_admin_stats_counts(client, admin_enabled):
    admin_tokens = await login(client, ADMIN_TG_ID)
    other_tokens = await login(client, OTHER_TG_ID)
    await client.post("/habits", json={"name": "Read"}, headers=bearer(other_tokens))
    await client.post("/rooms", json={"name": "Room A"}, headers=bearer(other_tokens))

    response = await client.get("/admin/stats", headers=bearer(admin_tokens))
    assert response.status_code == 200
    assert response.json() == {"total_users": 2, "total_rooms": 1, "total_habits": 1}


async def test_admin_lists_users_and_user_detail(client, admin_enabled):
    admin_tokens = await login(client, ADMIN_TG_ID)
    other_tokens = await login(client, OTHER_TG_ID)
    await client.post("/habits", json={"name": "Read"}, headers=bearer(other_tokens))

    response = await client.get("/admin/users", headers=bearer(admin_tokens))
    assert response.status_code == 200
    users = response.json()
    assert {u["username"] for u in users} == {f"alice{ADMIN_TG_ID}", f"alice{OTHER_TG_ID}"}

    other_id = next(u["id"] for u in users if u["username"] == f"alice{OTHER_TG_ID}")
    today = date.today()
    response = await client.get(
        f"/admin/users/{other_id}?from={today}&to={today}", headers=bearer(admin_tokens)
    )
    assert response.status_code == 200
    detail = response.json()
    assert detail["user"]["id"] == other_id
    assert [h["habit"]["name"] for h in detail["habits"]] == ["Read"]

    response = await client.get(
        f"/admin/users/999999?from={today}&to={today}", headers=bearer(admin_tokens)
    )
    assert response.status_code == 404


async def test_admin_lists_rooms_and_room_detail(client, admin_enabled):
    admin_tokens = await login(client, ADMIN_TG_ID)
    other_tokens = await login(client, OTHER_TG_ID)
    room = (
        await client.post("/rooms", json={"name": "Room A"}, headers=bearer(other_tokens))
    ).json()

    response = await client.get("/admin/rooms", headers=bearer(admin_tokens))
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) == 1
    assert rooms[0]["room"]["name"] == "Room A"
    assert rooms[0]["owner"]["username"] == f"alice{OTHER_TG_ID}"
    assert rooms[0]["member_count"] == 1

    response = await client.get(f"/admin/rooms/{room['id']}", headers=bearer(admin_tokens))
    assert response.status_code == 200
    detail = response.json()
    assert detail["room"]["id"] == room["id"]
    assert detail["owner"]["username"] == f"alice{OTHER_TG_ID}"
    assert [m["role"] for m in detail["members"]] == ["owner"]
    assert detail["habits"] == []

    response = await client.get("/admin/rooms/999999", headers=bearer(admin_tokens))
    assert response.status_code == 404
