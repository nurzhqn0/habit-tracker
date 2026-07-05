"""Seeds a demo user with realistic habits and 90 days of entries.

Usage: uv run python scripts/seed.py
"""

import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.models.entry import SKIP, YES_MANUAL  # noqa: E402
from app.infrastructure.db.base import create_engine, create_session_factory  # noqa: E402
from app.infrastructure.db.tables import Base, EntryRow, HabitRow, UserPreferencesRow, UserRow  # noqa: E402

HABITS = [
    dict(name="Meditate", question="Did you meditate today?", color=13, rate=0.85),
    dict(name="Exercise", question="Did you work out?", color=1, freq_num=3, freq_den=7, rate=0.5),
    dict(name="Read", type=1, target_value=20, unit="pages", color=10, rate=0.75),
    dict(name="Drink water", type=1, target_value=2, unit="L", color=9, rate=0.9),
    dict(name="No junk food", color=7, rate=0.7),
]


async def main() -> None:
    engine = create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = create_session_factory(engine)
    random.seed(42)
    today = datetime.now(UTC).date()

    async with factory() as session:
        user = UserRow(telegram_id=111_222_333, first_name="Demo", username="demo", bot_linked=False)
        session.add(user)
        await session.flush()
        session.add(UserPreferencesRow(user_id=user.id, skip_days_enabled=True))

        for position, spec in enumerate(HABITS):
            rate = spec.pop("rate")
            habit = HabitRow(user_id=user.id, uuid=f"demo{position}", position=position, **spec)
            session.add(habit)
            await session.flush()

            for offset in range(90):
                day = today - timedelta(days=offset)
                roll = random.random()
                if habit.type == 1:
                    if roll < rate:
                        value = int(habit.target_value * random.uniform(0.6, 1.5) * 1000)
                    elif roll < rate + 0.05:
                        value = SKIP
                    else:
                        continue
                else:
                    if roll < rate:
                        value = YES_MANUAL
                    elif roll < rate + 0.05:
                        value = SKIP
                    else:
                        continue
                session.add(EntryRow(habit_id=habit.id, date=day, value=value))

        await session.commit()
        print(f"Seeded demo user telegram_id=111222333 with {len(HABITS)} habits × 90 days")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
