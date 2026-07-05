"""Golden tests transcribed from uhabits EntryListTest.kt."""

from datetime import date, timedelta

from app.domain.models.entry import NO, SKIP, UNKNOWN, YES_AUTO, YES_MANUAL, Entry
from app.domain.models.frequency import DAILY, TWO_TIMES_PER_WEEK, WEEKLY, Frequency
from app.domain.services.entry_list import (
    Interval,
    build_entries_from_interval,
    build_intervals,
    compute_entries,
    get_by_interval,
    get_known,
    snap_intervals_together,
)

TODAY = date(2015, 1, 25)


def day(offset: int) -> date:
    return TODAY - timedelta(days=offset)


def test_get_by_interval_and_known():
    entries = {}
    entries[day(0)] = Entry(day(0), 15)
    entries[day(5)] = Entry(day(5), 20)
    entries[day(8)] = Entry(day(8), 30)

    known = get_known(entries)
    assert known == [Entry(day(0), 15), Entry(day(5), 20), Entry(day(8), 30)]

    actual = get_by_interval(entries, day(5), day(0))
    assert actual == [
        Entry(day(0), 15),
        Entry(day(1), UNKNOWN),
        Entry(day(2), UNKNOWN),
        Entry(day(3), UNKNOWN),
        Entry(day(4), UNKNOWN),
        Entry(day(5), 20),
    ]


def test_compute_boolean():
    original = {
        day(4): Entry(day(4), YES_MANUAL),
        day(9): Entry(day(9), YES_MANUAL),
        day(10): Entry(day(10), YES_MANUAL),
    }
    computed = compute_entries(original, Frequency(1, 3), is_numerical=False)
    assert get_known(computed) == [
        Entry(day(2), YES_AUTO),
        Entry(day(3), YES_AUTO),
        Entry(day(4), YES_MANUAL),
        Entry(day(7), YES_AUTO),
        Entry(day(8), YES_AUTO),
        Entry(day(9), YES_MANUAL),
        Entry(day(10), YES_MANUAL),
        Entry(day(11), YES_AUTO),
        Entry(day(12), YES_AUTO),
    ]

    assert compute_entries({}, Frequency(1, 3), is_numerical=False) == {}


def test_compute_numerical():
    original = {
        day(4): Entry(day(4), 100),
        day(9): Entry(day(9), 200),
        day(10): Entry(day(10), 300),
    }
    computed = compute_entries(original, DAILY, is_numerical=True)
    assert get_known(computed) == [Entry(day(4), 100), Entry(day(9), 200), Entry(day(10), 300)]


def test_build_entries_from_interval():
    entries = [
        Entry(day(1), YES_MANUAL),
        Entry(day(2), NO, "Test"),
        Entry(day(4), NO),
        Entry(day(5), YES_MANUAL),
        Entry(day(10), YES_MANUAL),
        Entry(day(11), NO),
    ]
    intervals = [
        Interval(day(2), day(2), day(1)),
        Interval(day(6), day(5), day(4)),
        Interval(day(10), day(8), day(8)),
    ]
    expected = [
        Entry(day(1), YES_MANUAL),
        Entry(day(2), YES_AUTO, "Test"),
        Entry(day(3), UNKNOWN),
        Entry(day(4), YES_AUTO),
        Entry(day(5), YES_MANUAL),
        Entry(day(6), YES_AUTO),
        Entry(day(7), UNKNOWN),
        Entry(day(8), YES_AUTO),
        Entry(day(9), YES_AUTO),
        Entry(day(10), YES_MANUAL),
        Entry(day(11), NO),
    ]
    assert build_entries_from_interval(entries, intervals) == expected


def test_snap_intervals_together_1():
    intervals = [
        Interval(day(8), day(8), day(2)),
        Interval(day(12), day(12), day(6)),
        Interval(day(20), day(20), day(14)),
        Interval(day(27), day(27), day(21)),
    ]
    snap_intervals_together(intervals)
    assert intervals == [
        Interval(day(8), day(8), day(2)),
        Interval(day(15), day(12), day(9)),
        Interval(day(22), day(20), day(16)),
        Interval(day(29), day(27), day(23)),
    ]


def test_snap_intervals_together_2():
    intervals = [
        Interval(day(6), day(4), day(0)),
        Interval(day(11), day(8), day(5)),
    ]
    snap_intervals_together(intervals)
    assert intervals == [
        Interval(day(6), day(4), day(0)),
        Interval(day(13), day(8), day(7)),
    ]


def test_build_intervals_weekly():
    entries = [Entry(day(8), YES_MANUAL), Entry(day(18), YES_MANUAL), Entry(day(23), YES_MANUAL)]
    assert build_intervals(WEEKLY, entries) == [
        Interval(day(8), day(8), day(2)),
        Interval(day(18), day(18), day(12)),
        Interval(day(23), day(23), day(17)),
    ]


def test_build_intervals_daily():
    entries = [Entry(day(8), YES_MANUAL), Entry(day(18), YES_MANUAL), Entry(day(23), YES_MANUAL)]
    assert build_intervals(DAILY, entries) == [
        Interval(day(8), day(8), day(8)),
        Interval(day(18), day(18), day(18)),
        Interval(day(23), day(23), day(23)),
    ]


def test_build_intervals_two_per_week():
    entries = [
        Entry(day(8), YES_MANUAL),
        Entry(day(15), YES_MANUAL),
        Entry(day(18), YES_MANUAL),
        Entry(day(22), YES_MANUAL),
        Entry(day(23), YES_MANUAL),
    ]
    assert build_intervals(TWO_TIMES_PER_WEEK, entries) == [
        Interval(day(18), day(15), day(12)),
        Interval(day(22), day(18), day(16)),
        Interval(day(23), day(22), day(17)),
    ]


def test_build_intervals_skips_ignored():
    entries = [Entry(day(10), YES_MANUAL), Entry(day(20), SKIP), Entry(day(30), YES_MANUAL)]
    assert build_intervals(Frequency(1, 3), entries) == [
        Interval(day(10), day(10), day(8)),
        Interval(day(30), day(30), day(28)),
    ]
