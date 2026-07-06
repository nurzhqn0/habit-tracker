"""Bot "Done" must write target*1000 for numerical habits, YES_MANUAL for yes/no."""

from app.domain.models.entry import YES_MANUAL
from app.infrastructure.db.tables import HabitRow
from app.workers.bot.handlers import done_value


def test_yes_no_habit_writes_yes_manual():
    habit = HabitRow(type=0)
    assert done_value(habit) == YES_MANUAL


def test_numerical_habit_writes_target_millis():
    habit = HabitRow(type=1, target_value=10.0)
    assert done_value(habit) == 10000


def test_numerical_fractional_target():
    habit = HabitRow(type=1, target_value=2.5)
    assert done_value(habit) == 2500
