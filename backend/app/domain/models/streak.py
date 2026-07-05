from dataclasses import dataclass
from datetime import date as Date


@dataclass(frozen=True)
class Streak:
    start: Date
    end: Date

    @property
    def length(self) -> int:
        return (self.end - self.start).days + 1
