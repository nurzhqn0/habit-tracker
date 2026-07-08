"""find_due_reminders with a frozen now_utc across timezones, masks, and completion states."""

from datetime import UTC, datetime

import pytest

from app.infrastructure.db.base import create_engine, create_session_factory
from app.infrastructure.db.tables import Base, EntryRow, HabitRow, UserPreferencesRow, UserRow
from app.workers.bot.reminders import find_due_reminders

# Frozen instant: 2026-07-06 09:00 UTC — a Monday. Almaty (UTC+5) local 14:00.
NOW = datetime(2026, 7, 6, 9, 0, tzinfo=UTC)


@pytest.fixture
async def session_factory():
    engine = create_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield create_session_factory(engine)
    await engine.dispose()


async def seed(
    session,
    telegram_id=1,
    timezone="UTC",
    bot_linked=True,
    reminders_enabled=True,
    hour=9,
    minute=0,
    days=127,
):
    user = UserRow(telegram_id=telegram_id, first_name="U", bot_linked=bot_linked)
    session.add(user)
    await session.flush()
    session.add(UserPreferencesRow(user_id=user.id, timezone=timezone, reminders_enabled=reminders_enabled))
    habit = HabitRow(
        user_id=user.id, uuid=f"u{telegram_id}", name="Habit",
        reminder_hour=hour, reminder_min=minute, reminder_days=days,
    )
    session.add(habit)
    await session.flush()
    return user, habit


async def test_due_at_exact_local_minute(session_factory):
    async with session_factory() as session:
        await seed(session, timezone="UTC", hour=9, minute=0)
        await seed(session, telegram_id=2, timezone="UTC", hour=9, minute=1)  # not yet
        await session.commit()
        due = await find_due_reminders(session, NOW)
    assert [d.telegram_id for d in due] == [1]


async def test_timezone_awareness(session_factory):
    async with session_factory() as session:
        # Almaty is UTC+5 → local 14:00 at the frozen instant.
        await seed(session, telegram_id=1, timezone="Asia/Almaty", hour=14, minute=0)
        await seed(session, telegram_id=2, timezone="Asia/Almaty", hour=9, minute=0)  # local 9am ≠ now
        await session.commit()
        due = await find_due_reminders(session, NOW)
    assert [d.telegram_id for d in due] == [1]


async def test_weekday_mask(session_factory):
    async with session_factory() as session:
        await seed(session, telegram_id=1, days=1)  # Monday-only bit 0 — NOW is a Monday
        await seed(session, telegram_id=2, days=1 << 1)  # Tuesday only
        await session.commit()
        due = await find_due_reminders(session, NOW)
    assert [d.telegram_id for d in due] == [1]


async def test_skips_completed_and_gates(session_factory):
    async with session_factory() as session:
        _, habit = await seed(session, telegram_id=1)  # completed today
        session.add(EntryRow(habit_id=habit.id, date=NOW.date(), value=2))
        await seed(session, telegram_id=2, bot_linked=False)
        await seed(session, telegram_id=3, reminders_enabled=False)
        await seed(session, telegram_id=5)  # the only eligible one
        await session.commit()
        due = await find_due_reminders(session, NOW)
    assert [d.telegram_id for d in due] == [5]


async def test_skip_entry_counts_as_handled(session_factory):
    async with session_factory() as session:
        _, habit = await seed(session, telegram_id=1)
        session.add(EntryRow(habit_id=habit.id, date=NOW.date(), value=3))  # SKIP
        await session.commit()
        due = await find_due_reminders(session, NOW)
    assert due == []
