"""Port of uhabits EntryList.kt — computed entries with YES_AUTO auto-fill.

All list orderings mirror the Kotlin original: "newest first" everywhere.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from app.domain.models.entry import SKIP, UNKNOWN, YES_AUTO, YES_MANUAL, Entry
from app.domain.models.frequency import Frequency


@dataclass(frozen=True)
class Interval:
    begin: Date
    center: Date
    end: Date

    @property
    def length(self) -> int:
        return (self.end - self.begin).days + 1


def _month_length(d: Date) -> int:
    return monthrange(d.year, d.month)[1]


def get_known(entries_by_date: dict[Date, Entry]) -> list[Entry]:
    """All known entries, newest first."""
    return sorted(entries_by_date.values(), key=lambda e: e.date, reverse=True)


def get_by_interval(entries_by_date: dict[Date, Entry], from_date: Date, to_date: Date) -> list[Entry]:
    """One entry per day in [from_date, to_date], newest first; missing days are UNKNOWN."""
    result: list[Entry] = []
    if from_date > to_date:
        return result
    current = to_date
    while current >= from_date:
        result.append(entries_by_date.get(current) or Entry(current, UNKNOWN))
        current -= timedelta(days=1)
    return result


def build_intervals(freq: Frequency, entries: list[Entry]) -> list[Interval]:
    """`entries` must be sorted newest first (as returned by get_known)."""
    filtered = [e for e in entries if e.value == YES_MANUAL]
    num = freq.numerator
    den = freq.denominator
    intervals: list[Interval] = []
    for i in range(num - 1, len(filtered)):
        begin = filtered[i].date
        center = filtered[i - num + 1].date
        size = den
        if den in (30, 31):
            if begin.day == _month_length(begin):
                size = _month_length(begin + timedelta(days=1))
            else:
                size = _month_length(begin)
        if (center - begin).days < size:
            end = begin + timedelta(days=size - 1)
            intervals.append(Interval(begin, center, end))
    return intervals


def snap_intervals_together(intervals: list[Interval]) -> None:
    """Slides intervals backwards into the past to eliminate gaps and maximize streaks.

    Intervals must be sorted newest first. Mutates the list in place.
    """
    for i in range(1, len(intervals)):
        curr = intervals[i]
        nxt = intervals[i - 1]
        gap_next_to_current = (curr.end - nxt.begin).days
        gap_center_to_end = (curr.end - curr.center).days
        if gap_next_to_current >= 0:
            shift = min(gap_center_to_end, gap_next_to_current + 1)
            intervals[i] = Interval(
                curr.begin - timedelta(days=shift),
                curr.center,
                curr.end - timedelta(days=shift),
            )


def build_entries_from_interval(original: list[Entry], intervals: list[Interval]) -> list[Entry]:
    """`original` and `intervals` sorted newest first. Returns entries newest first."""
    result: list[Entry] = []
    if not original:
        return result

    from_date = original[0].date
    to_date = original[0].date
    for e in original:
        if e.date < from_date:
            from_date = e.date
        if e.date > to_date:
            to_date = e.date
    for interval in intervals:
        if interval.begin < from_date:
            from_date = interval.begin
        if interval.end > to_date:
            to_date = interval.end

    current = to_date
    while current >= from_date:
        result.append(Entry(current, UNKNOWN))
        current -= timedelta(days=1)

    for interval in intervals:
        current = interval.end
        while current >= interval.begin:
            offset = (to_date - current).days
            result[offset] = Entry(current, YES_AUTO)
            current -= timedelta(days=1)

    for entry in original:
        offset = (to_date - entry.date).days
        if result[offset].value == UNKNOWN or entry.value in (SKIP, YES_MANUAL):
            value = entry.value
        else:
            value = YES_AUTO
        result[offset] = Entry(entry.date, value, entry.notes)

    return result


def compute_entries(
    original_by_date: dict[Date, Entry], frequency: Frequency, is_numerical: bool
) -> dict[Date, Entry]:
    """Port of EntryList.recomputeFrom — returns the computed entries map.

    Numerical habits: entries copied as-is. Boolean habits: YES_AUTO days filled
    per frequency intervals, snapped together to maximize streaks.
    """
    original = get_known(original_by_date)
    if is_numerical:
        return {e.date: e for e in original}

    intervals = build_intervals(frequency, original)
    snap_intervals_together(intervals)
    computed = build_entries_from_interval(original, intervals)
    return {e.date: e for e in computed if e.value != UNKNOWN or e.notes}
