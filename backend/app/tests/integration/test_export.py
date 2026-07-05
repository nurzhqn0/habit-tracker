import io
import zipfile
from datetime import UTC, datetime, timedelta

from openpyxl import load_workbook

from app.tests.integration.conftest import bearer, login

TODAY = datetime.now(UTC).date()


async def seed(client, headers):
    habit = (
        await client.post(
            "/habits", json={"name": "Meditate", "question": "Did you meditate?"}, headers=headers
        )
    ).json()
    numeric = (
        await client.post(
            "/habits", json={"name": "Read", "type": 1, "target_value": 20, "unit": "pages"},
            headers=headers,
        )
    ).json()
    for offset in range(3):
        d = TODAY - timedelta(days=offset)
        await client.post(f"/habits/{habit['id']}/entries/{d}/toggle", headers=headers)
    await client.put(
        f"/habits/{numeric['id']}/entries/{TODAY}",
        json={"value": 25000, "notes": "long session"},
        headers=headers,
    )
    return habit, numeric


async def test_csv_export_layout(client):
    headers = bearer(await login(client, 4000))
    await seed(client, headers)

    response = await client.get("/export/csv", headers=headers)
    assert response.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert "Habits.csv" in names
    assert "001 Meditate/Checkmarks.csv" in names
    assert "001 Meditate/Scores.csv" in names
    assert "002 Read/Checkmarks.csv" in names

    habits_csv = zf.read("Habits.csv").decode()
    assert "Meditate" in habits_csv and "NUMERICAL" in habits_csv

    checkmarks = zf.read("001 Meditate/Checkmarks.csv").decode()
    assert "YES_MANUAL" in checkmarks


async def test_csv_round_trip(client):
    headers = bearer(await login(client, 4001))
    await seed(client, headers)
    exported = (await client.get("/export/csv", headers=headers)).content

    # Import into a fresh user.
    headers_b = bearer(await login(client, 4002))
    response = await client.post(
        "/import/csv",
        files={"file": ("export.zip", exported, "application/zip")},
        headers=headers_b,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["habits_created"] == 2
    assert body["entries_imported"] == 4  # 3 toggles + 1 numeric

    habits = (await client.get("/habits", headers=headers_b)).json()
    assert {h["name"] for h in habits} == {"Meditate", "Read"}

    numeric = next(h for h in habits if h["name"] == "Read")
    assert numeric["type"] == 1
    assert numeric["target_value"] == 20.0

    entries = await client.get(
        f"/habits/{numeric['id']}/entries",
        params={"from": str(TODAY), "to": str(TODAY)},
        headers=headers_b,
    )
    assert entries.json()[0]["value"] == 25000
    assert entries.json()[0]["notes"] == "long session"


async def test_import_is_idempotent_by_name(client):
    headers = bearer(await login(client, 4003))
    await seed(client, headers)
    exported = (await client.get("/export/csv", headers=headers)).content

    first = (
        await client.post(
            "/import/csv", files={"file": ("e.zip", exported, "application/zip")}, headers=headers
        )
    ).json()
    assert first["habits_created"] == 0  # names already exist

    habits = (await client.get("/habits", headers=headers)).json()
    assert len(habits) == 2


async def test_import_rejects_garbage(client):
    headers = bearer(await login(client, 4004))
    response = await client.post(
        "/import/csv", files={"file": ("junk.zip", b"not a zip", "application/zip")}, headers=headers
    )
    assert response.status_code == 422


async def test_xlsx_export(client):
    headers = bearer(await login(client, 4005))
    await seed(client, headers)

    response = await client.get("/export/xlsx", headers=headers)
    assert response.status_code == 200
    workbook = load_workbook(io.BytesIO(response.content))
    assert "Habits" in workbook.sheetnames
    assert "Meditate" in workbook.sheetnames
    habits_sheet = workbook["Habits"]
    names = [row[1] for row in habits_sheet.iter_rows(min_row=2, values_only=True)]
    assert names == ["Meditate", "Read"]
