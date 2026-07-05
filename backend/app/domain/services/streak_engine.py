"""Port of uhabits StreakList."""

from datetime import date as Date
from datetime import timedelta

from app.domain.models.entry import UNKNOWN, Entry
from app.domain.models.habit import TargetType
from app.domain.models.streak import Streak
from app.domain.services.entry_list import get_by_interval


def compute_streaks(
    is_numerical: bool,
    target_type: TargetType,
    target_value: float,
    computed_entries: dict[Date, Entry],
    from_date: Date,
    to_date: Date,
) -> list[Streak]:
    """Returns streaks of consecutive successful days, newest first."""

    def successful(value: int) -> bool:
        if is_numerical:
            if target_type == TargetType.AT_LEAST:
                return value / 1000.0 >= target_value
            return value != UNKNOWN and value / 1000.0 <= target_value
        return value > 0

    dates = [e.date for e in get_by_interval(computed_entries, from_date, to_date) if successful(e.value)]
    if not dates:
        return []

    streaks: list[Streak] = []
    begin = dates[0]
    end = dates[0]
    for current in dates[1:]:
        if current == begin - timedelta(days=1):
            begin = current
        else:
            streaks.append(Streak(begin, end))
            begin = current
            end = current
    streaks.append(Streak(begin, end))
    return streaks


def best_streaks(streaks: list[Streak], limit: int) -> list[Streak]:
    """Top `limit` streaks by length (ties: newer wins), returned newest first."""
    ranked = sorted(streaks, key=lambda s: (s.length, s.end), reverse=True)
    return sorted(ranked[:limit], key=lambda s: s.end, reverse=True)
