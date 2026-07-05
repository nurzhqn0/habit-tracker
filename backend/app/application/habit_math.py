"""Bridges DB rows to the pure domain engine: computed entries, scores, streaks, today."""

from datetime import date as Date
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.models.entry import Entry
from app.domain.models.frequency import Frequency
from app.domain.models.habit import Habit, HabitType, TargetType
from app.domain.services.entry_list import compute_entries, get_known
from app.domain.services.score_engine import compute_scores
from app.domain.services.streak_engine import compute_streaks
from app.infrastructure.db.tables import EntryRow, HabitRow, UserPreferencesRow


def to_domain(row: HabitRow) -> Habit:
    return Habit(
        id=row.id,
        user_id=row.user_id,
        uuid=row.uuid,
        name=row.name,
        question=row.question,
        description=row.description,
        type=HabitType(row.type),
        color=row.color,
        position=row.position,
        archived=row.archived,
        frequency=Frequency(row.freq_num, row.freq_den),
        reminder_hour=row.reminder_hour,
        reminder_min=row.reminder_min,
        reminder_days=row.reminder_days,
        target_type=TargetType(row.target_type),
        target_value=row.target_value,
        unit=row.unit,
    )


def user_today(prefs: UserPreferencesRow | None) -> Date:
    tz_name = prefs.timezone if prefs else "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


def original_entries_map(entry_rows: list[EntryRow]) -> dict[Date, Entry]:
    return {row.date: Entry(row.date, row.value, row.notes) for row in entry_rows}


def computed_entries_for(habit: Habit, entry_rows: list[EntryRow]) -> dict[Date, Entry]:
    return compute_entries(original_entries_map(entry_rows), habit.frequency, habit.is_numerical)


def scores_for(habit: Habit, computed: dict[Date, Entry], today: Date) -> list:
    """Scores from the oldest entry through max(today, newest entry), oldest first.

    Extending past `today` mirrors uhabits (which computes to today+30) and keeps
    entries dated slightly in the future (timezone edges) inside the window.
    """
    known = get_known(computed)
    if not known:
        return []
    oldest = known[-1].date
    to = max(today, known[0].date)
    if oldest > to:
        return []
    return compute_scores(
        habit.frequency, habit.is_numerical, habit.target_type, habit.target_value, computed, oldest, to
    )


def score_on(habit: Habit, computed: dict[Date, Entry], today: Date) -> float:
    scores = scores_for(habit, computed, today)
    if not scores:
        return 0.0
    index = (today - scores[0].date).days
    if index < 0:
        return 0.0
    return scores[min(index, len(scores) - 1)].value


def streaks_for(habit: Habit, computed: dict[Date, Entry], today: Date) -> list:
    known = get_known(computed)
    if not known:
        return []
    oldest = known[-1].date
    to = max(today, known[0].date)
    if oldest > to:
        return []
    return compute_streaks(
        habit.is_numerical, habit.target_type, habit.target_value, computed, oldest, to
    )


def current_streak(habit: Habit, computed: dict[Date, Entry], today: Date) -> int:
    streaks = streaks_for(habit, computed, today)
    if not streaks:
        return 0
    newest = streaks[0]
    # Current streak = one still alive today or yesterday.
    if (today - newest.end).days <= 1:
        return newest.length
    return 0
