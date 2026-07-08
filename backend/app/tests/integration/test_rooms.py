from datetime import UTC, datetime, timedelta

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

    # Feed is restricted to the owner and admins.
    assert (await client.get(f"/rooms/{room['id']}/feed", headers=member)).status_code == 403

    feed = (await client.get(f"/rooms/{room['id']}/feed", headers=owner)).json()
    types = [e["type"] for e in feed]
    assert "entry_completed" in types
    assert "member_joined" in types
    completed = next(e for e in feed if e["type"] == "entry_completed")
    assert completed["room_habit_name"] == "Run"
    assert completed["entry_date"] == str(TODAY)

    # Cursor pagination.
    first_page = (
        await client.get(f"/rooms/{room['id']}/feed", params={"limit": 2}, headers=owner)
    ).json()
    assert len(first_page) == 2
    second_page = (
        await client.get(
            f"/rooms/{room['id']}/feed",
            params={"limit": 10, "cursor": first_page[-1]["id"]},
            headers=owner,
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


async def test_admin_permissions(client):
    owner = bearer(await login(client, 5020))
    admin_tokens = await login(client, 5021)
    admin = bearer(admin_tokens)
    admin_id = admin_tokens["user"]["id"]
    member_tokens = await login(client, 5022)
    member = bearer(member_tokens)
    member_id = member_tokens["user"]["id"]
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=admin)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    # Member cannot promote anyone; owner promotes admin.
    assert (
        await client.patch(
            f"/rooms/{room['id']}/members/{member_id}", json={"role": "admin"}, headers=admin
        )
    ).status_code == 403
    assert (
        await client.patch(
            f"/rooms/{room['id']}/members/{admin_id}", json={"role": "admin"}, headers=owner
        )
    ).status_code == 204
    members = (await client.get(f"/rooms/{room['id']}/members", headers=owner)).json()
    assert next(m["role"] for m in members if m["user_id"] == admin_id) == "admin"

    # Admin can manage room habits and rotate the invite code.
    created = await client.post(f"/rooms/{room['id']}/habits", json={"name": "Run"}, headers=admin)
    assert created.status_code == 201
    assert (
        await client.patch(
            f"/rooms/{room['id']}/habits/{created.json()['id']}", json={"name": "Jog"}, headers=admin
        )
    ).status_code == 200
    assert (
        await client.delete(f"/rooms/{room['id']}/habits/{created.json()['id']}", headers=admin)
    ).status_code == 204
    assert (await client.post(f"/rooms/{room['id']}/invite/rotate", headers=admin)).status_code == 200

    # Admin can patch room settings but cannot delete the room or change roles.
    patched = await client.patch(f"/rooms/{room['id']}", json={"name": "Ours"}, headers=admin)
    assert patched.status_code == 200
    assert patched.json()["name"] == "Ours"
    assert (await client.delete(f"/rooms/{room['id']}", headers=admin)).status_code == 403
    assert (
        await client.patch(
            f"/rooms/{room['id']}/members/{member_id}", json={"role": "admin"}, headers=admin
        )
    ).status_code == 403

    # Second admin: admin cannot remove another admin, but can remove a plain member.
    second_admin_tokens = await login(client, 5023)
    second_admin = bearer(second_admin_tokens)
    second_admin_id = second_admin_tokens["user"]["id"]
    await client.post("/rooms/join", json={"code": (await client.get(f"/rooms/{room['id']}", headers=owner)).json()["invite_code"]}, headers=second_admin)
    await client.patch(
        f"/rooms/{room['id']}/members/{second_admin_id}", json={"role": "admin"}, headers=owner
    )
    assert (
        await client.delete(f"/rooms/{room['id']}/members/{second_admin_id}", headers=admin)
    ).status_code == 403
    assert (
        await client.delete(f"/rooms/{room['id']}/members/{member_id}", headers=admin)
    ).status_code == 204

    # Owner demotes the admin back to member.
    assert (
        await client.patch(
            f"/rooms/{room['id']}/members/{admin_id}", json={"role": "member"}, headers=owner
        )
    ).status_code == 204
    assert (await client.post(f"/rooms/{room['id']}/invite/rotate", headers=admin)).status_code == 403


async def test_transfer_ownership(client):
    owner_tokens = await login(client, 5024)
    owner = bearer(owner_tokens)
    owner_id = owner_tokens["user"]["id"]
    member_tokens = await login(client, 5025)
    member = bearer(member_tokens)
    member_id = member_tokens["user"]["id"]
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    # Non-owner cannot transfer; owner cannot change their own role.
    assert (
        await client.post(
            f"/rooms/{room['id']}/transfer-ownership", json={"user_id": member_id}, headers=member
        )
    ).status_code == 403
    assert (
        await client.patch(
            f"/rooms/{room['id']}/members/{owner_id}", json={"role": "member"}, headers=owner
        )
    ).status_code == 422

    transferred = await client.post(
        f"/rooms/{room['id']}/transfer-ownership", json={"user_id": member_id}, headers=owner
    )
    assert transferred.status_code == 200
    assert transferred.json()["owner_id"] == member_id

    members = (await client.get(f"/rooms/{room['id']}/members", headers=owner)).json()
    roles = {m["user_id"]: m["role"] for m in members}
    assert roles[member_id] == "owner"
    assert roles[owner_id] == "admin"

    # Old owner keeps admin powers but cannot delete the room anymore.
    assert (await client.post(f"/rooms/{room['id']}/invite/rotate", headers=owner)).status_code == 200
    assert (await client.delete(f"/rooms/{room['id']}", headers=owner)).status_code == 403


async def test_invite_by_username(client):
    owner = bearer(await login(client, 5030))
    member_tokens = await login(client, 5031)  # username alice5031
    member = bearer(member_tokens)
    outsider_tokens = await login(client, 5032)  # username alice5032, never joins
    assert outsider_tokens
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    url = f"/rooms/{room['id']}/invite"

    # Plain member cannot invite.
    assert (
        await client.post(url, json={"username": "alice5032"}, headers=member)
    ).status_code == 403

    # Unknown username.
    result = (await client.post(url, json={"username": "ghost"}, headers=owner)).json()
    assert result["status"] == "not_registered"
    assert result["username"] == "ghost"
    assert room["invite_code"] in result["link"]

    # Registered but bot not linked (and no bot in tests).
    result = (await client.post(url, json={"username": "alice5032"}, headers=owner)).json()
    assert result["status"] == "not_linked"

    # Existing member; "@" prefix and case are normalized.
    result = (await client.post(url, json={"username": "@ALICE5031"}, headers=owner)).json()
    assert result["status"] == "already_member"
    assert result["username"] == "ALICE5031"


STATS_PATHS = [
    "stats/overview", "stats/scores", "stats/history", "stats/bar", "stats/weekdays",
    "stats/frequency", "stats/streaks", "stats/target", "stats/notes",
]


async def test_member_habits_view_auth_matrix(client):
    owner = bearer(await login(client, 5040))
    admin_tokens = await login(client, 5041)
    admin = bearer(admin_tokens)
    admin_id = admin_tokens["user"]["id"]
    member_tokens = await login(client, 5042)
    member = bearer(member_tokens)
    member_id = member_tokens["user"]["id"]
    outsider = bearer(await login(client, 5043))

    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=admin)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)
    await client.patch(
        f"/rooms/{room['id']}/members/{admin_id}", json={"role": "admin"}, headers=owner
    )

    room_habit = (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "Read"}, headers=owner)
    ).json()
    habit_id = (
        await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=member)
    ).json()["habit_id"]
    await client.post(f"/habits/{habit_id}/entries/{TODAY}/toggle", headers=member)
    unlinked = (await client.post("/habits", json={"name": "Private"}, headers=member)).json()

    base = f"/rooms/{room['id']}/members/{member_id}"
    window = {"from": str(TODAY - timedelta(days=6)), "to": str(TODAY)}

    # Plain member and outsider are denied.
    assert (await client.get(f"{base}/overview", params=window, headers=member)).status_code == 403
    assert (await client.get(f"{base}/overview", params=window, headers=outsider)).status_code == 404
    assert (
        await client.get(f"{base}/habits/{habit_id}/stats/overview", headers=outsider)
    ).status_code == 404
    assert (
        await client.get(f"{base}/habits/{habit_id}/stats/overview", headers=member)
    ).status_code == 403

    # Admin and owner see exactly the linked habit.
    for viewer in (admin, owner):
        response = await client.get(f"{base}/overview", params=window, headers=viewer)
        assert response.status_code == 200, response.text
        items = response.json()
        assert [i["habit"]["id"] for i in items] == [habit_id]
        assert items[0]["entries"][str(TODAY)] == 2
        assert items[0]["score"] > 0

    # Admin can read habit info and every stats endpoint for the linked habit.
    info = await client.get(f"{base}/habits/{habit_id}", headers=admin)
    assert info.status_code == 200
    assert info.json()["id"] == habit_id
    for path in STATS_PATHS:
        assert (
            await client.get(f"{base}/habits/{habit_id}/{path}", headers=admin)
        ).status_code == 200, path

    # The member's unlinked personal habit stays invisible.
    assert (await client.get(f"{base}/habits/{unlinked['id']}", headers=admin)).status_code == 404
    assert (
        await client.get(f"{base}/habits/{unlinked['id']}/stats/overview", headers=admin)
    ).status_code == 404


async def test_member_habit_view_cross_room_denied(client):
    owner = bearer(await login(client, 5050))
    member_tokens = await login(client, 5051)
    member = bearer(member_tokens)
    member_id = member_tokens["user"]["id"]

    room_x = await make_room(client, owner, name="Room X")
    room_y = await make_room(client, owner, name="Room Y")
    await client.post("/rooms/join", json={"code": room_y["invite_code"]}, headers=member)
    room_habit = (
        await client.post(f"/rooms/{room_y['id']}/habits", json={"name": "Run"}, headers=owner)
    ).json()
    habit_id = (
        await client.post(
            f"/rooms/{room_y['id']}/habits/{room_habit['id']}/link", json={}, headers=member
        )
    ).json()["habit_id"]

    window = {"from": str(TODAY - timedelta(days=6)), "to": str(TODAY)}

    # Not a member of room X yet.
    assert (
        await client.get(
            f"/rooms/{room_x['id']}/members/{member_id}/overview", params=window, headers=owner
        )
    ).status_code == 404

    # After joining room X with no links there: empty overview, and the room-Y habit
    # is not reachable through the room-X path.
    await client.post("/rooms/join", json={"code": room_x["invite_code"]}, headers=member)
    response = await client.get(
        f"/rooms/{room_x['id']}/members/{member_id}/overview", params=window, headers=owner
    )
    assert response.status_code == 200
    assert response.json() == []
    assert (
        await client.get(
            f"/rooms/{room_x['id']}/members/{member_id}/habits/{habit_id}/stats/overview",
            headers=owner,
        )
    ).status_code == 404


async def test_room_visibility_flags(client):
    owner = bearer(await login(client, 5060))
    admin_tokens = await login(client, 5061)
    admin = bearer(admin_tokens)
    admin_id = admin_tokens["user"]["id"]
    member = bearer(await login(client, 5062))
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=admin)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)
    await client.patch(
        f"/rooms/{room['id']}/members/{admin_id}", json={"role": "admin"}, headers=owner
    )

    # Flags default to visible.
    assert room["show_leaderboard"] is True
    assert room["show_members"] is True
    assert (await client.get(f"/rooms/{room['id']}/leaderboard", headers=member)).status_code == 200
    assert len((await client.get(f"/rooms/{room['id']}/members", headers=member)).json()) == 3

    patched = await client.patch(
        f"/rooms/{room['id']}",
        json={"show_leaderboard": False, "show_members": False},
        headers=owner,
    )
    assert patched.status_code == 200
    assert patched.json()["show_leaderboard"] is False
    assert patched.json()["show_members"] is False

    # Plain member: leaderboard denied, member list shrinks to their own row.
    assert (await client.get(f"/rooms/{room['id']}/leaderboard", headers=member)).status_code == 403
    mine = (await client.get(f"/rooms/{room['id']}/members", headers=member)).json()
    assert len(mine) == 1
    assert mine[0]["role"] == "member"

    # Admin and owner keep full access.
    for viewer in (admin, owner):
        assert (
            await client.get(f"/rooms/{room['id']}/leaderboard", headers=viewer)
        ).status_code == 200
        assert len((await client.get(f"/rooms/{room['id']}/members", headers=viewer)).json()) == 3

    # Restoring the flags restores member access.
    await client.patch(
        f"/rooms/{room['id']}",
        json={"show_leaderboard": True, "show_members": True},
        headers=admin,  # admins may edit settings too
    )
    assert (await client.get(f"/rooms/{room['id']}/leaderboard", headers=member)).status_code == 200
    assert len((await client.get(f"/rooms/{room['id']}/members", headers=member)).json()) == 3


async def test_room_target_independent_of_personal_target(client):
    owner = bearer(await login(client, 5070))
    member = bearer(await login(client, 5071))
    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)

    room_habit = (
        await client.post(
            f"/rooms/{room['id']}/habits",
            json={"name": "Read", "type": 1, "target_value": 20, "unit": "pages"},
            headers=owner,
        )
    ).json()
    habit_id = (
        await client.post(f"/rooms/{room['id']}/habits/{room_habit['id']}/link", json={}, headers=member)
    ).json()["habit_id"]

    # Member raises their personal target; the room habit's target stays untouched.
    patched = await client.patch(
        f"/habits/{habit_id}", json={"target_value": 40}, headers=member
    )
    assert patched.json()["target_value"] == 40
    room_view = (await client.get(f"/rooms/{room['id']}/habits", headers=member)).json()
    assert room_view[0]["habit"]["target_value"] == 20

    # 30 pages: enough for the room target (20), not for the personal target (40).
    await client.put(f"/habits/{habit_id}/entries/{TODAY}", json={"value": 30000}, headers=member)

    board = (await client.get(f"/rooms/{room['id']}/leaderboard", headers=member)).json()
    member_row = next(r for r in board if r["linked_habits"] == 1 and r["completions"] > 0)
    assert member_row["completions"] == 1

    feed = (await client.get(f"/rooms/{room['id']}/feed", headers=owner)).json()
    assert sum(1 for e in feed if e["type"] == "entry_completed") == 1

    # Personally not done: streak stays 0.
    overview = (
        await client.get(
            "/habits/overview",
            params={"from": str(TODAY - timedelta(days=6)), "to": str(TODAY)},
            headers=member,
        )
    ).json()
    assert overview[0]["streak"] == 0


async def test_member_history_clamped_to_join_date(client):
    owner = bearer(await login(client, 5080))
    member_tokens = await login(client, 5081)
    member = bearer(member_tokens)
    member_id = member_tokens["user"]["id"]

    # Member records history BEFORE joining the room.
    habit = (await client.post("/habits", json={"name": "Run"}, headers=member)).json()
    for offset in (10, 9, 8):
        d = TODAY - timedelta(days=offset)
        await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=member)

    room = await make_room(client, owner)
    await client.post("/rooms/join", json={"code": room["invite_code"]}, headers=member)
    room_habit = (
        await client.post(f"/rooms/{room['id']}/habits", json={"name": "Run"}, headers=owner)
    ).json()
    await client.post(
        f"/rooms/{room['id']}/habits/{room_habit['id']}/link",
        json={"habit_id": habit["id"]},
        headers=member,
    )
    # One post-join completion.
    await client.post(f"/habits/{habit['id']}/entries/{TODAY}/toggle", headers=member)

    # Leaderboard (all time) counts only post-join entries.
    board = (
        await client.get(f"/rooms/{room['id']}/leaderboard", params={"period": "all"}, headers=owner)
    ).json()
    member_row = next(r for r in board if r["user_id"] == member_id)
    assert member_row["completions"] == 1

    base = f"/rooms/{room['id']}/members/{member_id}"
    window = {"from": str(TODAY - timedelta(days=14)), "to": str(TODAY)}
    items = (await client.get(f"{base}/overview", params=window, headers=owner)).json()
    assert items[0]["entries"] == {str(TODAY): 2}

    stats = (
        await client.get(f"{base}/habits/{habit['id']}/stats/overview", headers=owner)
    ).json()
    assert stats["total_count"] == 1

    # The member still sees their own full history on the personal endpoint.
    own = (
        await client.get(
            "/habits/overview",
            params={"from": str(TODAY - timedelta(days=14)), "to": str(TODAY)},
            headers=member,
        )
    ).json()
    assert len(own[0]["entries"]) == 4
