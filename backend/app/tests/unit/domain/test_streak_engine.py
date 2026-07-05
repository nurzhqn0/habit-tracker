from datetime import date, timedelta

from app.domain.models.entry import NO, SKIP, UNKNOWN, YES_AUTO, YES_MANUAL, Entry
from app.domain.models.habit import TargetType
from app.domain.models.streak import Streak
from app.domain.services.streak_engine import best_streaks, compute_streaks

TODAY = date(2015, 1, 25)


def day(offset: int) -> date:
    return TODAY - timedelta(days=offset)


def entries(values: dict[int, int]) -> dict:
    return {day(d): Entry(day(d), v) for d, v in values.items()}


def boolean_streaks(values: dict[int, int], from_days_ago: int) -> list[Streak]:
    return compute_streaks(
        False, TargetType.AT_LEAST, 0.0, entries(values), day(from_days_ago), TODAY
    )


def test_consecutive_days_merge():
    streaks = boolean_streaks({0: YES_MANUAL, 1: YES_MANUAL, 2: YES_MANUAL, 5: YES_MANUAL}, 10)
    assert streaks == [Streak(day(2), day(0)), Streak(day(5), day(5))]
    assert streaks[0].length == 3


def test_skip_and_auto_count_no_breaks():
    streaks = boolean_streaks({0: YES_MANUAL, 1: SKIP, 2: YES_AUTO, 3: NO, 4: YES_MANUAL}, 10)
    assert streaks == [Streak(day(2), day(0)), Streak(day(4), day(4))]


def test_numerical_at_least():
    streaks = compute_streaks(
        True, TargetType.AT_LEAST, 2.0, entries({0: 2000, 1: 1999, 2: 3000}), day(5), TODAY
    )
    assert streaks == [Streak(day(0), day(0)), Streak(day(2), day(2))]


def test_numerical_at_most():
    streaks = compute_streaks(
        True, TargetType.AT_MOST, 2.0, entries({0: 1000, 1: 5000, 2: 0, 3: UNKNOWN}), day(3), TODAY
    )
    # 0 <= 2.0 counts; UNKNOWN never counts; missing days are UNKNOWN.
    assert streaks == [Streak(day(0), day(0)), Streak(day(2), day(2))]


def test_best_streaks_ranking():
    streaks = [
        Streak(day(2), day(0)),  # length 3, newest
        Streak(day(10), day(6)),  # length 5
        Streak(day(20), day(18)),  # length 3, oldest
    ]
    best = best_streaks(streaks, 2)
    # Top 2 by length: the 5-day streak and the newer 3-day streak; output newest first.
    assert best == [Streak(day(2), day(0)), Streak(day(10), day(6))]
