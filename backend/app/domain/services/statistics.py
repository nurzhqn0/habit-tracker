"""Ports of uhabits chart-data helpers: groupedSum, countSkippedDays, weekday frequency,
plus date truncation used for score/bar chart bucketing.

first_weekday convention: 0=Monday .. 6=Sunday (matches user_preferences.first_weekday).
"""

from datetime import date as Date
from datetime import timedelta
from enum import Enum

from app.domain.models.entry import SKIP, YES_MANUAL, Entry


class TruncateField(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


def start_of_week(d: Date, first_weekday: int) -> Date:
    return d - timedelta(days=(d.weekday() - first_weekday) % 7)


def truncate_date(d: Date, field: TruncateField, first_weekday: int = 0) -> Date:
    if field == TruncateField.DAY:
        return d
    if field == TruncateField.WEEK:
        return start_of_week(d, first_weekday)
    if field == TruncateField.MONTH:
        return d.replace(day=1)
    if field == TruncateField.QUARTER:
        return d.replace(month=(d.month - 1) // 3 * 3 + 1, day=1)
    return d.replace(month=1, day=1)


def grouped_sum(
    entries: list[Entry], field: TruncateField, is_numerical: bool, first_weekday: int = 0
) -> list[Entry]:
    """Sum of entry values per truncated date. Boolean: YES_MANUAL -> 1000, else 0.
    Numerical: SKIP -> 0, else max(0, value). Newest first."""
    groups: dict[Date, int] = {}
    for e in entries:
        if is_numerical:
            value = 0 if e.value == SKIP else max(0, e.value)
        else:
            value = 1000 if e.value == YES_MANUAL else 0
        key = truncate_date(e.date, field, first_weekday)
        groups[key] = groups.get(key, 0) + value
    return [Entry(d, v) for d, v in sorted(groups.items(), reverse=True)]


def count_skipped_days(entries: list[Entry], field: TruncateField, first_weekday: int = 0) -> list[Entry]:
    """Number of SKIP days per truncated date. Newest first."""
    groups: dict[Date, int] = {}
    for e in entries:
        key = truncate_date(e.date, field, first_weekday)
        groups[key] = groups.get(key, 0) + (1 if e.value == SKIP else 0)
    return [Entry(d, v) for d, v in sorted(groups.items(), reverse=True)]


def compute_weekday_frequency(entries: list[Entry], is_numerical: bool) -> dict[Date, list[int]]:
    """Per month-start: 7 totals indexed Saturday=0, Sunday=1, ... Friday=6 (uhabits layout)."""
    result: dict[Date, list[int]] = {}
    for e in entries:
        weekday = (e.date.weekday() + 2) % 7
        month_start = e.date.replace(day=1)
        totals = result.setdefault(month_start, [0] * 7)
        if is_numerical:
            totals[weekday] += e.value
        elif e.value == YES_MANUAL:
            totals[weekday] += 1
    return result
