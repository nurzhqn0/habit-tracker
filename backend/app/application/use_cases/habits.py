from dataclasses import dataclass
from datetime import date as Date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application import habit_math
from app.domain.errors import ValidationError
from app.infrastructure.db.tables import HabitRow
from app.infrastructure.repositories.habit_repo import EntryRepo, HabitRepo
from app.infrastructure.repositories.user_repo import UserRepo

MUTABLE_FIELDS = {
    "name", "question", "description", "type", "color", "freq_num", "freq_den",
    "reminder_hour", "reminder_min", "reminder_days", "target_type", "target_value", "unit",
}


@dataclass
class HabitOverviewItem:
    habit: HabitRow
    score: float
    streak: int
    entries: dict[Date, int]
    notes: dict[Date, str]


def _validate(fields: dict) -> None:
    if "name" in fields and not str(fields["name"]).strip():
        raise ValidationError("Habit name must not be empty")
    if fields.get("freq_num", 1) < 1 or fields.get("freq_den", 1) < 1:
        raise ValidationError("Frequency must be positive")
    if fields.get("target_value", 0) is not None and fields.get("target_value", 0) < 0:
        raise ValidationError("Target must be non-negative")
    for key, upper in (("reminder_hour", 23), ("reminder_min", 59)):
        value = fields.get(key)
        if value is not None and not 0 <= value <= upper:
            raise ValidationError(f"{key} out of range")


async def create_habit(session: AsyncSession, user_id: int, fields: dict) -> HabitRow:
    _validate(fields)
    habit = await HabitRepo(session).create(user_id, **{k: v for k, v in fields.items() if k in MUTABLE_FIELDS})
    await session.commit()
    return habit


async def update_habit(session: AsyncSession, user_id: int, habit_id: int, fields: dict) -> HabitRow:
    _validate(fields)
    habit = await HabitRepo(session).get_owned(habit_id, user_id)
    for key, value in fields.items():
        if key in MUTABLE_FIELDS:
            setattr(habit, key, value)
    await session.commit()
    return habit


async def delete_habit(session: AsyncSession, user_id: int, habit_id: int) -> None:
    repo = HabitRepo(session)
    habit = await repo.get_owned(habit_id, user_id)
    await repo.delete(habit)
    await session.commit()


async def reorder_habits(session: AsyncSession, user_id: int, ordered_ids: list[int]) -> None:
    repo = HabitRepo(session)
    habits = {h.id: h for h in await repo.list_for_user(user_id)}
    if set(ordered_ids) != set(habits):
        raise ValidationError("ordered_ids must contain exactly all habit ids")
    for position, habit_id in enumerate(ordered_ids):
        habits[habit_id].position = position
    await session.commit()


async def get_overview(
    session: AsyncSession,
    user_id: int,
    from_date: Date,
    to_date: Date,
    sort: str = "manual",
    habit_ids: list[int] | None = None,
    since: Date | None = None,
) -> list[HabitOverviewItem]:
    """Bulk main-screen payload: every habit + computed entries in range + score + streak."""
    prefs = await UserRepo(session).get_or_create_preferences(user_id)
    today = habit_math.user_today(prefs)

    rows = await HabitRepo(session).list_for_user(user_id)
    if habit_ids is not None:
        wanted = set(habit_ids)
        rows = [r for r in rows if r.id in wanted]
    entries_by_habit = await EntryRepo(session).all_for_habits([r.id for r in rows])
    if since is not None:
        entries_by_habit = {
            habit_id: [r for r in rows_ if r.date >= since]
            for habit_id, rows_ in entries_by_habit.items()
        }

    items: list[HabitOverviewItem] = []
    for row in rows:
        habit = habit_math.to_domain(row)
        computed = habit_math.computed_entries_for(habit, entries_by_habit[row.id])
        window = {
            d: e for d, e in computed.items() if from_date <= d <= to_date
        }
        items.append(
            HabitOverviewItem(
                habit=row,
                score=habit_math.score_on(habit, computed, today),
                streak=habit_math.current_streak(habit, computed, today),
                entries={d: e.value for d, e in window.items()},
                notes={d: e.notes for d, e in window.items() if e.notes},
            )
        )

    if sort == "name":
        items.sort(key=lambda i: i.habit.name.lower())
    elif sort == "color":
        items.sort(key=lambda i: i.habit.color)
    elif sort == "score":
        items.sort(key=lambda i: -i.score)
    elif sort == "status":
        items.sort(key=lambda i: -(i.entries.get(today, -1)))
    return items
