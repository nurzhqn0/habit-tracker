from datetime import UTC, datetime, timedelta

import pytest

from app.tests.integration.conftest import bearer, login

TODAY = datetime.now(UTC).date()


async def seeded_habit(client, headers, days=3, **overrides):
    response = await client.post("/habits", json={"name": "Run", **overrides}, headers=headers)
    habit = response.json()
    for offset in range(days):
        d = TODAY - timedelta(days=offset)
        await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)
    return habit


async def test_overview_card(client):
    headers = bearer(await login(client, 3000))
    habit = await seeded_habit(client, headers, days=3)

    response = await client.get(f"/habits/{habit['id']}/stats/overview", headers=headers)
    body = response.json()
    # 3 daily checks: score = 0.147820 (golden value), diffs equal score (baseline 0).
    assert body["score_today"] == pytest.approx(0.147820, abs=1e-5)
    assert body["score_month_diff"] == pytest.approx(body["score_today"], abs=1e-9)
    assert body["total_count"] == 3
    assert body["streak"] == 3


async def test_scores_series_and_buckets(client):
    headers = bearer(await login(client, 3001))
    habit = await seeded_habit(client, headers, days=10)

    daily = (await client.get(f"/habits/{habit['id']}/stats/scores", headers=headers)).json()
    assert len(daily) == 10
    assert daily[0]["value"] == pytest.approx(0.051922, abs=1e-5)

    weekly = (
        await client.get(
            f"/habits/{habit['id']}/stats/scores", params={"bucket": "week"}, headers=headers
        )
    ).json()
    assert 2 <= len(weekly) <= 3


async def test_history_heatmap(client):
    headers = bearer(await login(client, 3002))
    habit = await seeded_habit(client, headers, days=2)

    body = (await client.get(f"/habits/{habit['id']}/stats/history", headers=headers)).json()
    assert body["entries"][str(TODAY)] == 2
    assert body["today"] == str(TODAY)


async def test_bar_and_weekdays(client):
    headers = bearer(await login(client, 3003))
    habit = await seeded_habit(client, headers, days=3)

    bar = (
        await client.get(f"/habits/{habit['id']}/stats/bar", params={"bucket": "year"}, headers=headers)
    ).json()
    assert sum(b["value"] for b in bar) == 3000  # 3 x YES_MANUAL -> 1000 each

    weekdays = (await client.get(f"/habits/{habit['id']}/stats/weekdays", headers=headers)).json()
    assert len(weekdays) == 7
    assert sum(w["value"] for w in weekdays) == 3


async def test_streaks_endpoint(client):
    headers = bearer(await login(client, 3004))
    habit = await seeded_habit(client, headers, days=2)
    # A separate older streak.
    d = TODAY - timedelta(days=5)
    await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)

    body = (await client.get(f"/habits/{habit['id']}/stats/streaks", headers=headers)).json()
    assert [s["length"] for s in body] == [2, 1]  # newest first
    assert body[0]["end"] == str(TODAY)


async def test_target_card(client):
    headers = bearer(await login(client, 3005))
    habit = (
        await client.post(
            "/habits",
            json={"name": "Read", "type": 1, "target_value": 10, "unit": "pages"},
            headers=headers,
        )
    ).json()
    await client.put(
        f"/habits/{habit['id']}/entries/{TODAY}", json={"value": 25000}, headers=headers
    )

    body = (await client.get(f"/habits/{habit['id']}/stats/target", headers=headers)).json()
    week = next(r for r in body if r["period"] == "week")
    assert week["actual"] == 25.0
    assert week["target"] == 70.0  # 10/day * 7 days


async def test_notes_card(client):
    headers = bearer(await login(client, 3006))
    habit = (await client.post("/habits", json={"name": "Journal"}, headers=headers)).json()
    await client.put(
        f"/habits/{habit['id']}/entries/{TODAY}",
        json={"value": 2, "notes": "great session"},
        headers=headers,
    )

    body = (await client.get(f"/habits/{habit['id']}/stats/notes", headers=headers)).json()
    assert body == [{"date": str(TODAY), "value": 2, "notes": "great session", "skip": False}]


async def test_frequency_endpoint(client):
    headers = bearer(await login(client, 3009))
    habit = (await client.post("/habits", json={"name": "Pray"}, headers=headers)).json()
    # Fixed dates with known weekdays: 2026-05-30 Sat; 2026-06-01, 2026-06-08 Mon; 2026-06-07 Sun.
    for d in ("2026-05-30", "2026-06-01", "2026-06-08", "2026-06-07"):
        await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)

    body = (await client.get(f"/habits/{habit['id']}/stats/frequency", headers=headers)).json()
    assert [m["month"] for m in body] == ["2026-05", "2026-06"]
    # weekdays are Sunday-first: [Sun, Mon, Tue, Wed, Thu, Fri, Sat]
    assert body[0]["weekdays"] == [0, 0, 0, 0, 0, 0, 1]
    assert body[1]["weekdays"] == [1, 2, 0, 0, 0, 0, 0]


async def test_stats_cross_user_denied(client):
    headers_a = bearer(await login(client, 3007))
    headers_b = bearer(await login(client, 3008))
    habit = await seeded_habit(client, headers_a, days=1)

    for endpoint in (
        "overview", "scores", "history", "bar", "weekdays", "frequency", "streaks", "target", "notes",
    ):
        response = await client.get(f"/habits/{habit['id']}/stats/{endpoint}", headers=headers_b)
        assert response.status_code == 404, endpoint
