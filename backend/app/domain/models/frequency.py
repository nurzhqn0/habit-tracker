from dataclasses import dataclass


@dataclass(frozen=True)
class Frequency:
    """Habit frequency: numerator times per denominator days. num == den normalizes to daily."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator == self.denominator:
            object.__setattr__(self, "numerator", 1)
            object.__setattr__(self, "denominator", 1)

    def to_double(self) -> float:
        return self.numerator / self.denominator


DAILY = Frequency(1, 1)
THREE_TIMES_PER_WEEK = Frequency(3, 7)
TWO_TIMES_PER_WEEK = Frequency(2, 7)
WEEKLY = Frequency(1, 7)
