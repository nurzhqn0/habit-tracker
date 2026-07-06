"""Stats use cases — one function per detail-screen chart card."""

from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application import habit_math
from app.domain.models.entry import SKIP, YES_MANUAL, Entry
from app.domain.models.habit import Habit
from app.domain.services.statistics import (
    TruncateField,
    compute_weekday_frequency,
    count_skipped_days,
    grouped_sum,
)
from app.domain.services.streak_engine import best_streaks
from app.infrastructure.repositories.habit_repo import EntryRepo, HabitRepo
from app.infrastructure.repositories.user_repo import UserRepo


@dataclass
class StatsContext:
    habit: Habit
    computed: dict[Date, Entry]
    today: Date
    first_weekday: int


async def _context(session: AsyncSession, user_id: int, habit_id: int) -> StatsContext:
    habit_row = await HabitRepo(session).get_owned(habit_id, user_id)
    habit = habit_math.to_domain(habit_row)
    entry_rows = await EntryRepo(session).all_for_habit(habit_id)
    prefs = await UserRepo(session).get_or_create_preferences(user_id)
    return StatsContext(
        habit=habit,
        computed=habit_math.computed_entries_for(habit, entry_rows),
        today=habit_math.user_today(prefs),
        first_weekday=prefs.first_weekday,
    )


async def overview(session: AsyncSession, user_id: int, habit_id: int) -> dict:
    ctx = await _context(session, user_id, habit_id)
    scores = habit_math.scores_for(ctx.habit, ctx.computed, ctx.today)
    by_date = {s.date: s.value for s in scores}
    today_score = by_date.get(ctx.today, scores[-1].value if scores else 0.0)
    month_ago = by_date.get(ctx.today - timedelta(days=30), 0.0)
    year_ago = by_date.get(ctx.today - timedelta(days=365), 0.0)
    total = sum(
        1 for e in ctx.computed.values()
        if (e.value == YES_MANUAL if not ctx.habit.is_numerical else e.value > 0)
    )
    return {
        "score_today": today_score,
        "score_month_diff": today_score - month_ago,
        "score_year_diff": today_score - year_ago,
        "total_count": total,
        "streak": habit_math.current_streak(ctx.habit, ctx.computed, ctx.today),
    }


_BUCKETS = {
    "day": TruncateField.DAY,
    "week": TruncateField.WEEK,
    "month": TruncateField.MONTH,
    "quarter": TruncateField.QUARTER,
    "year": TruncateField.YEAR,
}


async def scores_series(
    session: AsyncSession, user_id: int, habit_id: int, bucket: str, from_date: Date | None
) -> list[dict]:
    ctx = await _context(session, user_id, habit_id)
    scores = habit_math.scores_for(ctx.habit, ctx.computed, ctx.today)
    if from_date:
        scores = [s for s in scores if s.date >= from_date]
    field = _BUCKETS[bucket]
    if field == TruncateField.DAY:
        return [{"date": s.date, "value": s.value} for s in scores]

    from app.domain.services.statistics import truncate_date

    groups: dict[Date, list[float]] = {}
    for s in scores:
        groups.setdefault(truncate_date(s.date, field, ctx.first_weekday), []).append(s.value)
    return [
        {"date": d, "value": sum(values) / len(values)} for d, values in sorted(groups.items())
    ]


async def history(session: AsyncSession, user_id: int, habit_id: int, year: int | None) -> dict:
    ctx = await _context(session, user_id, habit_id)
    entries = ctx.computed
    if year:
        entries = {d: e for d, e in entries.items() if d.year == year}
    return {
        "today": ctx.today,
        "first_weekday": ctx.first_weekday,
        "target_value": ctx.habit.target_value,
        "target_type": int(ctx.habit.target_type),
        "type": int(ctx.habit.type),
        "entries": {d.isoformat(): e.value for d, e in sorted(entries.items())},
    }


async def bar(session: AsyncSession, user_id: int, habit_id: int, bucket: str) -> list[dict]:
    ctx = await _context(session, user_id, habit_id)
    entries = sorted(ctx.computed.values(), key=lambda e: e.date, reverse=True)
    sums = grouped_sum(entries, _BUCKETS[bucket], ctx.habit.is_numerical, ctx.first_weekday)
    return [{"date": e.date, "value": e.value} for e in reversed(sums)]


async def weekdays(session: AsyncSession, user_id: int, habit_id: int) -> list[dict]:
    """Totals per weekday Mon..Sun across all history."""
    ctx = await _context(session, user_id, habit_id)
    totals = [0] * 7
    for e in ctx.computed.values():
        if ctx.habit.is_numerical:
            if e.value > 0:
                totals[e.date.weekday()] += e.value
        elif e.value == YES_MANUAL:
            totals[e.date.weekday()] += 1
    return [{"weekday": i, "value": totals[i]} for i in range(7)]


async def frequency(session: AsyncSession, user_id: int, habit_id: int) -> list[dict]:
    """Per-month weekday totals for the frequency dot chart. Weekdays Sunday-first."""
    ctx = await _context(session, user_id, habit_id)
    by_month = compute_weekday_frequency(list(ctx.computed.values()), ctx.habit.is_numerical)
    return [
        # uhabits layout is Saturday=0, Sunday=1 .. Friday=6; rotate to Sunday-first.
        {"month": month.isoformat()[:7], "weekdays": totals[1:] + totals[:1]}
        for month, totals in sorted(by_month.items())
    ]


async def streaks(session: AsyncSession, user_id: int, habit_id: int, limit: int) -> list[dict]:
    ctx = await _context(session, user_id, habit_id)
    all_streaks = habit_math.streaks_for(ctx.habit, ctx.computed, ctx.today)
    return [
        {"start": s.start, "end": s.end, "length": s.length}
        for s in best_streaks(all_streaks, limit)
    ]


async def target(session: AsyncSession, user_id: int, habit_id: int) -> list[dict]:
    """Numerical target card: actual vs adjusted target for week/month/quarter/year."""
    ctx = await _context(session, user_id, habit_id)
    habit = ctx.habit
    entries = sorted(ctx.computed.values(), key=lambda e: e.date, reverse=True)
    daily_target = habit.target_value / habit.frequency.denominator * habit.frequency.numerator

    result = []
    for label, field, days in (
        ("week", TruncateField.WEEK, 7),
        ("month", TruncateField.MONTH, 30),
        ("quarter", TruncateField.QUARTER, 91),
        ("year", TruncateField.YEAR, 365),
    ):
        sums = grouped_sum(entries, field, is_numerical=True, first_weekday=ctx.first_weekday)
        skips = count_skipped_days(entries, field, first_weekday=ctx.first_weekday)
        from app.domain.services.statistics import truncate_date

        period_start = truncate_date(ctx.today, field, ctx.first_weekday)
        actual = next((e.value / 1000 for e in sums if e.date == period_start), 0.0)
        skipped = next((e.value for e in skips if e.date == period_start), 0)
        result.append(
            {
                "period": label,
                "actual": actual,
                "target": max(0.0, daily_target * (days - skipped)),
            }
        )
    return result


async def notes(session: AsyncSession, user_id: int, habit_id: int, limit: int = 50) -> list[dict]:
    ctx = await _context(session, user_id, habit_id)
    with_notes = sorted(
        (e for e in ctx.computed.values() if e.notes), key=lambda e: e.date, reverse=True
    )
    return [
        {"date": e.date, "value": e.value, "notes": e.notes, "skip": e.value == SKIP}
        for e in with_notes[:limit]
    ]
