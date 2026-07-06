from datetime import UTC, datetime

from app.tests.integration.conftest import bearer, login

TODAY = datetime.now(UTC).date()


async def make_room(client, headers, name="Morning Crew"):
    response = await client.post("/rooms", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_room_lifecycle_and_join(client):
    owner = bearer(await login(client, 5000))
    friend = bearer(await login(client, 5001))

    room = await make_room(client, owner)
    assert room["invite_code"]

    # Non-member cannot see the room.
    assert (await client.get(f"/rooms/{room['id']}", headers=friend)).status_code == 404

    joined = await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=friend)
    assert joined.status_code == 200
    assert joined.json()["id"] == room["id"]

    members = (await client.get(f"/rooms/{room['id']}/members", headers=friend)).json()
    assert len(members) == 2
    assert {m["role"] for m in members} == {"owner", "member"}

    # Bad code rejected.
    assert (await client.post("/rooms/join", json={"code": "nope"}, headers=friend)).status_code == 404


async def test_owner_guards(client):
    owner = bearer(await login(client, 5002))
    member = bearer(await login(client, 5003))
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    # Member cannot patch/delete room, rotate invite, or create room habits.
    assert (
        await client.patch(f"/rooms/{room['id']}", json={"name": "Hacked"}, headers=member)
    ).status_code == 403
    assert (await client.delete(f"/rooms/{room['id']}", headers=member)).status_code == 403
    assert (
        await client.post(f"/rooms/{room['id']}/invite/rotate", headers=member)
    ).status_code == 403
    assert (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "X"}, headers=member)
    ).status_code == 403

    rotated = await client.post(f"/rooms/{room['id']}/invite/rotate", headers=owner)
    assert rotated.status_code == 200
    assert rotated.json()["invite_code"] != room["invite_code"]


async def test_link_and_create_from_template(client):
    owner = bearer(await login(client, 5004))
    member = bearer(await login(client, 5005))
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    room_habit = (
        await client.post(
            f"/rooms/{room['id']}/habits",
            json={"name": "Meditate", "freq_num": 1, "freq_den": 1, "color": 3},
            headers=owner,
        )
    ).json()

    # Member creates a personal habit from the template.
    linked = await client.post(
        f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=member
    )
    assert linked.status_code == 200
    created_habit_id = linked.json()["habit_id"]
    my_habits = (await client.get("/habits", headers=member)).json()
    assert any(h["id"] == created_habit_id and h["name"] == "Meditate" for h in my_habits)

    # Double link rejected.
    assert (
        await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=member)
    ).status_code == 409

    # Owner links an existing personal habit.
    own_habit = (await client.post("/habits", json={"name": "My meditation"}, headers=owner)).json()
    linked_owner = await client.post(
        f"/rooms/{room['id']}/habits/{room_habit['id']}/link",
        json={"habit_id": own_habit["id"]},
        headers=owner,
    )
    assert linked_owner.status_code == 200

    habits_view = (await client.get(f"/rooms/{room['id']}/habits", headers=member)).json()
    assert habits_view[0]["members_linked"] == 2
    assert habits_view[0]["linked_habit_id"] == created_habit_id

    # Unlink.
    assert (
        await client.delete(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", headers=member)
    ).status_code == 204


async def test_link_rejects_type_mismatch(client):
    owner = bearer(await login(client, 5014))
    room = await make_room(client, owner)

    # Yes/no room habit, numerical personal habit.
    room_habit = (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "Read"}, headers=owner)
    ).json()
    numerical = (
        await client.post(
            "/habits",
            json={"name": "Pages", "type": 1, "target_value": 10, "unit": "pages"},
            headers=owner,
        )
    ).json()

    response = await client.post(
        f"/rooms/{room['id']}/habits/{room_habit['id']}/link",
        json={"habit_id": numerical["id"]},
        headers=owner,
    )
    assert response.status_code == 422


async def test_leaderboard_and_feed(client):
    owner = bearer(await login(client, 5006))
    member = bearer(await login(client, 5007))
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    room_habit = (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "Run"}, headers=owner)
    ).json()
    owner_habit = (
        await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=owner)
    ).json()["habit_id"]
    await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=member)

    # Owner completes today on the linked habit.
    await client.post(f"/habits/{owner_habit}/entries/{TODAY}/toggle", headers=owner)

    board = (await client.get(f"/rooms/{room['id']}/leaderboard", headers=member)).json()
    assert len(board) == 2
    assert board[0]["completions"] == 1  # owner leads
    assert board[0]["score"] > board[1]["score"]

    feed = (await client.get(f"/rooms/{room['id']}/feed", headers=member)).json()
    types = [e["type"] for e in feed]
    assert "entry_completed" in types
    assert "member_joined" in types
    completed = next(e for e in feed if e["type"] == "entry_completed")
    assert completed["room_habit_name"] == "Run"
    assert completed["entry_date"] == str(TODAY)

    # Cursor pagination.
    first_page = (
        await client.get(f"/rooms/{room['id']}/feed", params={"limit": 2}, headers=member)
    ).json()
    assert len(first_page) == 2
    second_page = (
        await client.get(
            f"/rooms/{room['id']}/feed",
            params={"limit": 10, "cursor": first_page[-1]["id"]},
            headers=member,
        )
    ).json()
    assert all(e["id"] < first_page[-1]["id"] for e in second_page)


async def test_toggle_off_does_not_double_fire_event(client):
    owner = bearer(await login(client, 5008))
    room = await make_room(client, owner)
    room_habit = (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "Run"}, headers=owner)
    ).json()
    habit_id = (
        await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=owner)
    ).json()["habit_id"]

    url = f"/habits/{habit_id}/entries/{TODAY}/toggle"
    await client.post(url, headers=owner)  # YES -> event
    await client.post(url, headers=owner)  # NO
    await client.post(url, headers=owner)  # YES -> second event

    feed = (await client.get(f"/rooms/{room['id']}/feed", headers=owner)).json()
    assert sum(1 for e in feed if e["type"] == "entry_completed") == 2


async def test_member_removal_and_leave(client):
    owner = bearer(await login(client, 5009))
    member_tokens = await login(client, 5010)
    member = bearer(member_tokens)
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    # Member cannot kick others; owner cannot be removed.
    owner_id = (await client.get("/me", headers=owner)).json()["id"]
    member_id = member_tokens["user"]["id"]
    assert (
        await client.delete(f"/rooms/{room['id']}/members/{owner_id}", headers=member)
    ).status_code in (403, 422)

    # Member leaves.
    assert (
        await client.delete(f"/rooms/{room['id']}/members/{member_id}", headers=member)
    ).status_code == 204
    assert (await client.get(f"/rooms/{room['id']}", headers=member)).status_code == 404
