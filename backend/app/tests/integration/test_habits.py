from datetime import UTC, datetime, timedelta

from app.tests.integration.conftest import bearer, login

# Server "today" is computed in the user's preference timezone (UTC by default).
TODAY = datetime.now(UTC).date()


async def create_habit(client, headers, **overrides):
    body = {"name": "Meditate", **overrides}
    response = await client.post("/habits", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_habit_crud(client):
    headers = bearer(await login(client, 2000))

    habit = await create_habit(client, headers, question="Did you meditate?", color=3)
    assert habit["color"] == 3
    assert habit["uuid"]

    patched = await client.patch(f"/habits/{habit['id']}", json={"name": "Meditate AM"}, headers=headers)
    assert patched.json()["name"] == "Meditate AM"

    archived = await client.post(f"/habits/{habit['id']}/archive", headers=headers)
    assert archived.json()["archived"] is True
    active = await client.get("/habits", params={"archived": False}, headers=headers)
    assert active.json() == []

    deleted = await client.delete(f"/habits/{habit['id']}", headers=headers)
    assert deleted.status_code == 204
    assert (await client.get(f"/habits/{habit['id']}", headers=headers)).status_code == 404


async def test_cross_user_access_denied(client):
    headers_a = bearer(await login(client, 2001))
    headers_b = bearer(await login(client, 2002))
    habit = await create_habit(client, headers_a)

    assert (await client.get(f"/habits/{habit['id']}", headers=headers_b)).status_code == 404
    assert (
        await client.patch(f"/habits/{habit['id']}", json={"name": "Stolen"}, headers=headers_b)
    ).status_code == 404
    assert (
        await client.post(f"/habits/{habit['id']}/entries/{TODAY}/toggle", headers=headers_b)
    ).status_code == 404


async def test_toggle_cycle_default_prefs(client):
    headers = bearer(await login(client, 2003))
    habit = await create_habit(client, headers)
    url = f"/habits/{habit['id']}/entries/{TODAY}/toggle"

    # Default prefs: no skips, no question marks → UNKNOWN → YES_MANUAL → NO → YES_MANUAL
    assert (await client.post(url, headers=headers)).json()["value"] == 2
    assert (await client.post(url, headers=headers)).json()["value"] == 0
    assert (await client.post(url, headers=headers)).json()["value"] == 2


async def test_toggle_cycle_with_skip_and_question_marks(client):
    headers = bearer(await login(client, 2004))
    await client.patch(
        "/me/preferences", json={"skip_days_enabled": True, "show_question_marks": True}, headers=headers
    )
    habit = await create_habit(client, headers)
    url = f"/habits/{habit['id']}/entries/{TODAY}/toggle"

    # UNKNOWN → YES_MANUAL → SKIP → NO → UNKNOWN → YES_MANUAL
    for expected in (2, 3, 0, -1, 2):
        assert (await client.post(url, headers=headers)).json()["value"] == expected


async def test_streak_and_score_in_overview(client):
    headers = bearer(await login(client, 2005))
    habit = await create_habit(client, headers)

    for offset in range(3):
        d = TODAY - timedelta(days=offset)
        await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)

    response = await client.get(
        "/habits/overview",
        params={"from": str(TODAY - timedelta(days=6)), "to": str(TODAY)},
        headers=headers,
    )
    assert response.status_code == 200
    item = response.json()[0]
    assert item["streak"] == 3
    assert 0.1 < item["score"] < 0.2  # 3 daily checks ≈ 0.1477
    assert item["entries"][str(TODAY)] == 2


async def test_numerical_habit_progress(client):
    headers = bearer(await login(client, 2006))
    habit = await create_habit(
        client, headers, name="Read", type=1, target_value=20, unit="pages"
    )

    put = await client.put(
        f"/habits/{habit['id']}/entries/{TODAY}",
        json={"value": 20000, "notes": "finished chapter"},
        headers=headers,
    )
    assert put.status_code == 200
    assert put.json()["streak"] == 1

    # Toggle rejected for numerical habits.
    toggle = await client.post(f"/habits/{habit['id']}/entries/{TODAY}/toggle", headers=headers)
    assert toggle.status_code == 422

    entries = await client.get(
        f"/habits/{habit['id']}/entries",
        params={"from": str(TODAY), "to": str(TODAY)},
        headers=headers,
    )
    assert entries.json() == [{"date": str(TODAY), "value": 20000, "notes": "finished chapter"}]


async def test_reorder(client):
    headers = bearer(await login(client, 2007))
    first = await create_habit(client, headers, name="A")
    second = await create_habit(client, headers, name="B")

    response = await client.put(
        "/habits/positions", json={"ordered_ids": [second["id"], first["id"]]}, headers=headers
    )
    assert response.status_code == 204

    ordered = await client.get("/habits", headers=headers)
    assert [h["name"] for h in ordered.json()] == ["B", "A"]

    bad = await client.put("/habits/positions", json={"ordered_ids": [first["id"]]}, headers=headers)
    assert bad.status_code == 422


async def test_yes_auto_fill_for_weekly_habit(client):
    headers = bearer(await login(client, 2008))
    habit = await create_habit(client, headers, name="Weekly", freq_num=1, freq_den=7)

    d = TODAY - timedelta(days=3)
    await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)

    entries = await client.get(
        f"/habits/{habit['id']}/entries",
        params={"from": str(TODAY - timedelta(days=10)), "to": str(TODAY)},
        headers=headers,
    )
    values = {e["date"]: e["value"] for e in entries.json()}
    assert values[str(d)] == 2
    # The 6 days after the manual check are auto-filled (weekly frequency).
    assert values[str(d + timedelta(days=1))] == 1
    assert values[str(d + timedelta(days=3))] == 1
