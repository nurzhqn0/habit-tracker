from dataclasses import dataclass
from datetime import date as Date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application import habit_math
from app.application.use_cases.rooms import record_entry_activity
from app.domain.errors import ValidationError
from app.domain.models.entry import UNKNOWN, next_toggle_value
from app.infrastructure.repositories.habit_repo import EntryRepo, HabitRepo
from app.infrastructure.repositories.user_repo import UserRepo


@dataclass
class EntryChange:
    value: int
    score: float
    streak: int
    entries: dict[Date, int]  # refreshed computed values (YES_AUTO fill may shift)


async def _refreshed(session: AsyncSession, habit_row, user_id: int) -> tuple[float, int, dict]:
    habit = habit_math.to_domain(habit_row)
    entry_rows = await EntryRepo(session).all_for_habit(habit_row.id)
    computed = habit_math.computed_entries_for(habit, entry_rows)
    prefs = await UserRepo(session).get_or_create_preferences(user_id)
    today = habit_math.user_today(prefs)
    return (
        habit_math.score_on(habit, computed, today),
        habit_math.current_streak(habit, computed, today),
        {d: e.value for d, e in computed.items()},
    )


async def get_computed_entries(
    session: AsyncSession, user_id: int, habit_id: int, from_date: Date, to_date: Date
) -> dict[Date, tuple[int, str]]:
    habit_row = await HabitRepo(session).get_owned(habit_id, user_id)
    habit = habit_math.to_domain(habit_row)
    entry_rows = await EntryRepo(session).all_for_habit(habit_id)
    computed = habit_math.computed_entries_for(habit, entry_rows)
    return {
        d: (e.value, e.notes) for d, e in computed.items() if from_date <= d <= to_date
    }


async def upsert_entry(
    session: AsyncSession, user_id: int, habit_id: int, date: Date, value: int, notes: str | None
) -> EntryChange:
    habit_row = await HabitRepo(session).get_owned(habit_id, user_id)
    if habit_row.type == 0 and value not in (-1, 0, 1, 2, 3):
        raise ValidationError("Invalid value for a yes/no habit")
    if habit_row.type == 1 and value < -1:
        raise ValidationError("Invalid value for a numerical habit")

    repo = EntryRepo(session)
    existing = await repo.get(habit_id, date)
    previous_value = existing.value if existing else UNKNOWN
    if value == UNKNOWN and not notes:
        await repo.delete(habit_id, date)
    else:
        await repo.upsert(habit_id, date, value, notes)
    await record_entry_activity(session, user_id, habit_row, date, value, previous_value)
    await session.commit()

    score, streak, entries = await _refreshed(session, habit_row, user_id)
    return EntryChange(value=value, score=score, streak=streak, entries=entries)


async def toggle_entry(session: AsyncSession, user_id: int, habit_id: int, date: Date) -> EntryChange:
    habit_row = await HabitRepo(session).get_owned(habit_id, user_id)
    if habit_row.type != 0:
        raise ValidationError("Toggle applies only to yes/no habits; use PUT for numerical")

    habit = habit_math.to_domain(habit_row)
    prefs = await UserRepo(session).get_or_create_preferences(user_id)
    entry_rows = await EntryRepo(session).all_for_habit(habit_id)
    computed = habit_math.computed_entries_for(habit, entry_rows)

    current = computed[date].value if date in computed else UNKNOWN
    next_value = next_toggle_value(current, prefs.skip_days_enabled, prefs.show_question_marks)

    repo = EntryRepo(session)
    existing = await repo.get(habit_id, date)
    if next_value == UNKNOWN and not (existing and existing.notes):
        await repo.delete(habit_id, date)
    else:
        await repo.upsert(habit_id, date, next_value)
    await record_entry_activity(session, user_id, habit_row, date, next_value, current)
    await session.commit()

    score, streak, entries = await _refreshed(session, habit_row, user_id)
    return EntryChange(value=next_value, score=score, streak=streak, entries=entries)


async def delete_entry(session: AsyncSession, user_id: int, habit_id: int, date: Date) -> EntryChange:
    habit_row = await HabitRepo(session).get_owned(habit_id, user_id)
    await EntryRepo(session).delete(habit_id, date)
    await session.commit()
    score, streak, entries = await _refreshed(session, habit_row, user_id)
    return EntryChange(value=UNKNOWN, score=score, streak=streak, entries=entries)
