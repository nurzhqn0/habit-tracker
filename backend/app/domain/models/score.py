from dataclasses import dataclass
from datetime import date as Date
from math import sqrt


@dataclass(frozen=True)
class Score:
    date: Date
    value: float


def compute(frequency: float, previous_score: float, checkmark_value: float) -> float:
    """Port of uhabits Score.compute — exponential moving average.

    The multiplier is the daily decay; 13.0 is the smoothing constant used by uhabits.
    """
    multiplier = 0.5 ** (sqrt(frequency) / 13.0)
    return previous_score * multiplier + checkmark_value * (1 - multiplier)
