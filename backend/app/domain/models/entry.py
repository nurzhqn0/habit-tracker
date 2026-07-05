from dataclasses import dataclass
from datetime import date as Date

UNKNOWN = -1
NO = 0
YES_AUTO = 1
YES_MANUAL = 2
SKIP = 3


@dataclass(frozen=True)
class Entry:
    date: Date
    value: int
    notes: str = ""


def next_toggle_value(value: int, is_skip_enabled: bool, are_question_marks_enabled: bool) -> int:
    """Port of uhabits Entry.nextToggleValue."""
    if value == YES_AUTO:
        return YES_MANUAL
    if value == YES_MANUAL:
        return SKIP if is_skip_enabled else NO
    if value == SKIP:
        return NO
    if value == NO:
        return UNKNOWN if are_question_marks_enabled else YES_MANUAL
    return YES_MANUAL
