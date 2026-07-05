from dataclasses import dataclass, field
from enum import IntEnum

from app.domain.models.frequency import DAILY, Frequency


class HabitType(IntEnum):
    YES_NO = 0
    NUMERICAL = 1


class TargetType(IntEnum):
    AT_LEAST = 0
    AT_MOST = 1


@dataclass
class Habit:
    id: int | None = None
    user_id: int | None = None
    uuid: str = ""
    name: str = ""
    question: str = ""
    description: str = ""
    type: HabitType = HabitType.YES_NO
    color: int = 8
    position: int = 0
    archived: bool = False
    frequency: Frequency = field(default_factory=lambda: DAILY)
    reminder_hour: int | None = None
    reminder_min: int | None = None
    reminder_days: int = 127
    target_type: TargetType = TargetType.AT_LEAST
    target_value: float = 0.0
    unit: str = ""

    @property
    def is_numerical(self) -> bool:
        return self.type == HabitType.NUMERICAL
