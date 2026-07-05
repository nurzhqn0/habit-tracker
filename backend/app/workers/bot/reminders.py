"""Due-reminder computation. Pure of aiogram — testable with a frozen `now_utc`.

Weekday mask convention: bit i set = reminder fires on weekday i (Mon=0 .. Sun=6),
matching the frontend ReminderPicker.
"""

from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application import habit_math
from app.infrastructure.db.tables import HabitRow, UserPreferencesRow, UserRow
from app.infrastructure.repositories.habit_repo import EntryRepo


@dataclass
class DueReminder:
    telegram_id: int
    user_id: int
    habit_id: int
    habit_name: str
    question: str
    is_numerical: bool
    local_date: Date


def _local_now(now_utc: datetime, tz_name: str) -> datetime:
    try:
        return now_utc.astimezone(ZoneInfo(tz_name))
    except (ZoneInfoNotFoundError, ValueError):
        return now_utc.astimezone(ZoneInfo("UTC"))


async def find_due_reminders(session: AsyncSession, now_utc: datetime) -> list[DueReminder]:
    query = (
        select(HabitRow, UserRow, UserPreferencesRow)
        .join(UserRow, HabitRow.user_id == UserRow.id)
        .join(UserPreferencesRow, UserPreferencesRow.user_id == UserRow.id)
        .where(
            HabitRow.archived.is_(False),
            HabitRow.reminder_hour.is_not(None),
            UserRow.bot_linked.is_(True),
            UserPreferencesRow.reminders_enabled.is_(True),
        )
    )
    rows = (await session.execute(query)).all()

    due: list[DueReminder] = []
    entry_repo = EntryRepo(session)

    for habit_row, user_row, prefs in rows:
        local = _local_now(now_utc, prefs.timezone)
        if habit_row.reminder_hour != local.hour or (habit_row.reminder_min or 0) != local.minute:
            continue
        if not (habit_row.reminder_days >> local.weekday()) & 1:
            continue

        # Skip habits already completed (or skipped) today.
        habit = habit_math.to_domain(habit_row)
        entry_rows = await entry_repo.all_for_habit(habit_row.id)
        computed = habit_math.computed_entries_for(habit, entry_rows)
        today_entry = computed.get(local.date())
        if today_entry is not None and today_entry.value > 0:
            continue

        due.append(
            DueReminder(
                telegram_id=user_row.telegram_id,
                user_id=user_row.id,
                habit_id=habit_row.id,
                habit_name=habit_row.name,
                question=habit_row.question,
                is_numerical=habit_row.type == 1,
                local_date=local.date(),
            )
        )
    return due
