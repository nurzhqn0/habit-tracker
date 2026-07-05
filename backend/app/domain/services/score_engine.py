"""Port of uhabits ScoreList.recompute."""

from datetime import date as Date
from datetime import timedelta

from app.domain.models.entry import SKIP, YES_MANUAL, Entry
from app.domain.models.frequency import Frequency
from app.domain.models.habit import TargetType
from app.domain.models.score import Score, compute
from app.domain.services.entry_list import get_by_interval


def compute_scores(
    frequency: Frequency,
    is_numerical: bool,
    target_type: TargetType,
    target_value: float,
    computed_entries: dict[Date, Entry],
    from_date: Date,
    to_date: Date,
) -> list[Score]:
    """Returns one score per day in [from_date, to_date], oldest first."""
    if from_date > to_date:
        return []

    rolling_sum = 0.0
    numerator = frequency.numerator
    denominator = frequency.denominator
    freq = frequency.to_double()
    values = [e.value for e in get_by_interval(computed_entries, from_date, to_date)]  # newest first
    is_at_most = target_type == TargetType.AT_MOST

    # For non-daily boolean habits, double numerator and denominator to smooth out
    # irregular repetition schedules (uhabits behavior).
    if not is_numerical and freq < 1.0:
        numerator *= 2
        denominator *= 2

    previous_value = 1.0 if (is_numerical and is_at_most) else 0.0
    scores: list[Score] = []

    for i in range(len(values)):
        offset = len(values) - i - 1
        if is_numerical:
            rolling_sum += max(0, values[offset])
            if offset + denominator < len(values):
                rolling_sum -= max(0, values[offset + denominator])

            normalized_rolling_sum = rolling_sum / 1000
            if values[offset] != SKIP:
                if not is_at_most:
                    if target_value > 0:
                        percentage_completed = min(1.0, normalized_rolling_sum / target_value)
                    else:
                        percentage_completed = 1.0
                else:
                    if target_value > 0:
                        percentage_completed = max(
                            0.0, min(1.0, 1 - ((normalized_rolling_sum - target_value) / target_value))
                        )
                    else:
                        percentage_completed = 0.0 if normalized_rolling_sum > 0 else 1.0
                previous_value = compute(freq, previous_value, percentage_completed)
        else:
            if values[offset] == YES_MANUAL:
                rolling_sum += 1.0
            if offset + denominator < len(values):
                if values[offset + denominator] == YES_MANUAL:
                    rolling_sum -= 1.0
            if values[offset] != SKIP:
                percentage_completed = min(1.0, rolling_sum / numerator)
                previous_value = compute(freq, previous_value, percentage_completed)

        scores.append(Score(from_date + timedelta(days=i), previous_value))

    return scores
