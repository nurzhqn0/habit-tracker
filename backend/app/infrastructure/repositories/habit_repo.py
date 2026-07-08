import uuid as uuid_lib
from datetime import date as Date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import NotFoundError
from app.infrastructure.db.tables import EntryRow, HabitRow


class HabitRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: int) -> list[HabitRow]:
        query = (
            select(HabitRow)
            .where(HabitRow.user_id == user_id)
            .order_by(HabitRow.position, HabitRow.id)
        )
        return list((await self.session.execute(query)).scalars())

    async def get_owned(self, habit_id: int, user_id: int) -> HabitRow:
        habit = await self.session.get(HabitRow, habit_id)
        if habit is None or habit.user_id != user_id:
            raise NotFoundError("Habit not found")
        return habit

    async def create(self, user_id: int, **fields) -> HabitRow:
        max_position = await self.session.scalar(
            select(func.coalesce(func.max(HabitRow.position), -1)).where(HabitRow.user_id == user_id)
        )
        habit = HabitRow(user_id=user_id, uuid=uuid_lib.uuid4().hex, position=max_position + 1, **fields)
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def delete(self, habit: HabitRow) -> None:
        await self.session.execute(delete(EntryRow).where(EntryRow.habit_id == habit.id))
        await self.session.delete(habit)
        await self.session.flush()


class EntryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def all_for_habit(self, habit_id: int) -> list[EntryRow]:
        query = select(EntryRow).where(EntryRow.habit_id == habit_id)
        return list((await self.session.execute(query)).scalars())

    async def all_for_habits(self, habit_ids: list[int]) -> dict[int, list[EntryRow]]:
        if not habit_ids:
            return {}
        query = select(EntryRow).where(EntryRow.habit_id.in_(habit_ids))
        result: dict[int, list[EntryRow]] = {habit_id: [] for habit_id in habit_ids}
        for row in (await self.session.execute(query)).scalars():
            result[row.habit_id].append(row)
        return result

    async def get(self, habit_id: int, date: Date) -> EntryRow | None:
        query = select(EntryRow).where(EntryRow.habit_id == habit_id, EntryRow.date == date)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def upsert(self, habit_id: int, date: Date, value: int, notes: str | None = None) -> EntryRow:
        row = await self.get(habit_id, date)
        if row is None:
            row = EntryRow(habit_id=habit_id, date=date, value=value, notes=notes or "")
            self.session.add(row)
        else:
            row.value = value
            if notes is not None:
                row.notes = notes
        await self.session.flush()
        return row

    async def delete(self, habit_id: int, date: Date) -> None:
        row = await self.get(habit_id, date)
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()
