"""Golden tests transcribed from uhabits ScoreListTest.kt.

Harness mirrors uhabits Habit.recompute: computed entries derived from originals,
scores computed from the oldest known entry through today; dates outside that
range score 0. Numerical test habits use targetValue=2.0 (uhabits fixture).
"""

from datetime import date, timedelta

import pytest

from app.domain.models.entry import NO, SKIP, YES_MANUAL, Entry
from app.domain.models.frequency import DAILY, WEEKLY, Frequency
from app.domain.models.habit import TargetType
from app.domain.services.entry_list import compute_entries, get_known
from app.domain.services.score_engine import compute_scores

TODAY = date(2015, 1, 25)
E = 1e-6


def day(offset: int) -> date:
    return TODAY - timedelta(days=offset)


def score_fn(
    original: dict,
    frequency: Frequency = DAILY,
    is_numerical: bool = False,
    target_type: TargetType = TargetType.AT_LEAST,
    target_value: float = 2.0,
):
    """Returns score_at(days_ago) for the given habit setup."""
    computed = compute_entries(original, frequency, is_numerical)
    known = get_known(original)
    if not known:
        return lambda days_ago: 0.0
    oldest = known[-1].date
    scores = compute_scores(frequency, is_numerical, target_type, target_value, computed, oldest, TODAY)
    by_date = {s.date: s.value for s in scores}
    return lambda days_ago: by_date.get(day(days_ago), 0.0)


def checks(days: list[int]) -> dict:
    return {day(d): Entry(day(d), YES_MANUAL) for d in days}


def numeric(pairs: dict[int, int]) -> dict:
    return {day(d): Entry(day(d), v) for d, v in pairs.items()}


def assert_scores(score_at, expected: list[float], epsilon: float = E):
    for days_ago, value in enumerate(expected):
        assert score_at(days_ago) == pytest.approx(value, abs=epsilon), f"day -{days_ago}"


def test_yes_no_get_value():
    score_at = score_fn(checks(list(range(20))))
    assert_scores(
        score_at,
        [
            0.655747, 0.636894, 0.617008, 0.596033, 0.573910, 0.550574, 0.525961, 0.500000,
            0.472617, 0.443734, 0.413270, 0.381137, 0.347244, 0.311495, 0.273788, 0.234017,
            0.192067, 0.147820, 0.101149, 0.051922, 0.000000, 0.000000, 0.000000,
        ],
    )


def test_yes_no_with_skip():
    original = checks(list(range(20)))
    for d in (5, 10, 11):
        original[day(d)] = Entry(day(d), SKIP)
    score_at = score_fn(original)
    assert_scores(
        score_at,
        [
            0.596033, 0.573910, 0.550574, 0.525961, 0.500000, 0.472617, 0.472617, 0.443734,
            0.413270, 0.381137, 0.347244, 0.347244, 0.347244, 0.311495, 0.273788, 0.234017,
            0.192067, 0.147820, 0.101149, 0.051922, 0.000000, 0.000000, 0.000000,
        ],
    )


def test_yes_no_with_skip_2():
    original = checks([5])
    original[day(4)] = Entry(day(4), SKIP)
    score_at = score_fn(original)
    assert_scores(score_at, [0.041949, 0.044247, 0.046670, 0.049226, 0.051922, 0.051922, 0.0])


def test_imperfect_non_daily():
    # 3x/week habit with 1 missed repetition per week converges to 66%.
    pattern = [YES_MANUAL, YES_MANUAL, NO, NO, NO, NO, NO] * 100
    original = checks([i for i, v in enumerate(pattern) if v == YES_MANUAL])
    score_at = score_fn(original, frequency=Frequency(3, 7))
    assert score_at(0) == pytest.approx(2 / 3.0, abs=E)

    score_at = score_fn(original, frequency=Frequency(4, 7))
    assert score_at(0) == pytest.approx(0.5, abs=E)


def test_irregular_non_daily():
    # Perfect weekly habit on varying weekdays still converges to 100%.
    pattern = ([YES_MANUAL] + [NO] * 6 + [NO] * 6 + [YES_MANUAL]) * 100
    original = checks([i for i, v in enumerate(pattern) if v == YES_MANUAL])
    score_at = score_fn(original, frequency=WEEKLY)
    assert score_at(0) == pytest.approx(1.0, abs=1e-3)


def test_high_score_in_reasonable_time():
    assert score_fn(checks(list(range(90))))(0) > 0.99
    assert score_fn(checks([7 * i for i in range(39)]), frequency=WEEKLY)(0) > 0.99
    assert score_fn(checks([30 * i for i in range(18)]), frequency=Frequency(1, 30))(0) > 0.99


def test_yes_no_recompute_with_frequency_change():
    original = checks([0, 1])
    assert score_fn(original)(0) == pytest.approx(0.101149, abs=E)
    assert score_fn(original, frequency=Frequency(1, 2))(0) == pytest.approx(0.054816, abs=E)


def test_numerical_at_least_get_value():
    score_at = score_fn(numeric({d: 2000 for d in range(20)}), is_numerical=True)
    assert_scores(
        score_at,
        [
            0.655747, 0.636894, 0.617008, 0.596033, 0.573910, 0.550574, 0.525961, 0.500000,
            0.472617, 0.443734, 0.413270, 0.381137, 0.347244, 0.311495, 0.273788, 0.234017,
            0.192067, 0.147820, 0.101149, 0.051922, 0.000000, 0.000000, 0.000000,
        ],
    )


def test_numerical_at_least_recompute():
    original = numeric({0: 2000, 1: 2000})
    assert score_fn(original, is_numerical=True)(0) == pytest.approx(0.101149, abs=E)
    assert score_fn(original, is_numerical=True, frequency=Frequency(1, 2))(0) == pytest.approx(
        0.072631, abs=E
    )


def test_numerical_at_least_comparable_to_progress():
    assert score_fn(numeric({d: 1000 for d in range(500)}), is_numerical=True)(0) == pytest.approx(
        0.5, abs=E
    )
    assert score_fn(numeric({d: 500 for d in range(500)}), is_numerical=True)(0) == pytest.approx(
        0.25, abs=E
    )


def test_numerical_overachieving_is_not_relevant():
    assert score_fn(numeric({0: 10_000_000}), is_numerical=True)(0) == pytest.approx(0.051922, abs=E)


def test_numerical_at_least_with_skips():
    pairs = {d: 2000 for d in range(20)}
    pairs[10] = SKIP
    pairs[15] = SKIP
    score_at = score_fn(numeric(pairs), is_numerical=True)
    assert_scores(
        score_at,
        [
            0.617008, 0.596033, 0.573910, 0.550574, 0.525961, 0.500000, 0.472617, 0.443734,
            0.413270, 0.381137, 0.347244, 0.347244, 0.311495, 0.273788, 0.234017, 0.192067,
            0.192067, 0.147820, 0.101149, 0.051922, 0.000000, 0.000000, 0.000000,
        ],
    )


def test_numerical_skips_do_not_affect_score():
    baseline = score_fn(numeric({d: 1000 for d in range(500)}), is_numerical=True)(0)

    pairs = {d: 1000 for d in range(500)} | {d: SKIP for d in range(500, 1000)}
    assert score_fn(numeric(pairs), is_numerical=True)(0) == pytest.approx(baseline, abs=E)

    pairs = (
        {d: 1000 for d in range(300)}
        | {d: SKIP for d in range(300, 500)}
        | {d: 1000 for d in range(500, 700)}
    )
    assert score_fn(numeric(pairs), is_numerical=True)(0) == pytest.approx(baseline, abs=E)


def test_at_most_get_value():
    pairs = {20: 1000} | {d: 5000 for d in range(20)}
    score_at = score_fn(numeric(pairs), is_numerical=True, target_type=TargetType.AT_MOST)
    assert_scores(
        score_at,
        [
            0.344253, 0.363106, 0.382992, 0.403967, 0.426090, 0.449426, 0.474039, 0.500000,
            0.527383, 0.556266, 0.586730, 0.618863, 0.652756, 0.688505, 0.726212, 0.765983,
            0.807933, 0.852180, 0.898851, 0.948078, 1.0, 0.0, 0.0,
        ],
    )


def test_at_most_recompute():
    original = numeric({0: 5000, 1: 5000})
    assert score_fn(original, is_numerical=True, target_type=TargetType.AT_MOST)(0) == pytest.approx(
        0.898850, abs=E
    )
    assert score_fn(
        original, is_numerical=True, target_type=TargetType.AT_MOST, frequency=Frequency(1, 2)
    )(0) == pytest.approx(0.927369, abs=E)


def test_at_most_comparable_to_progress():
    assert score_fn(
        numeric({d: 3000 for d in range(500)}), is_numerical=True, target_type=TargetType.AT_MOST
    )(0) == pytest.approx(0.5, abs=E)
    assert score_fn(
        numeric({d: 3500 for d in range(500)}), is_numerical=True, target_type=TargetType.AT_MOST
    )(0) == pytest.approx(0.25, abs=E)


def test_at_most_undereachieving_is_not_relevant():
    assert score_fn(
        numeric({1: 10_000_000}), is_numerical=True, target_type=TargetType.AT_MOST
    )(0) == pytest.approx(0.950773, abs=E)


def test_at_most_overachieving_is_not_relevant():
    original = numeric({0: 5000, 1: 0})
    assert score_fn(original, is_numerical=True, target_type=TargetType.AT_MOST)(0) == pytest.approx(
        0.948077, abs=E
    )
    original = numeric({0: 5000, 1: 1000})
    assert score_fn(original, is_numerical=True, target_type=TargetType.AT_MOST)(0) == pytest.approx(
        0.948077, abs=E
    )
