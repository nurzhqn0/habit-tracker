from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.tables import HabitRow, RoomMemberRow, RoomRow, UserRow


class AdminRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def counts(self) -> tuple[int, int, int]:
        users = (await self.session.execute(select(func.count()).select_from(UserRow))).scalar_one()
        rooms = (await self.session.execute(select(func.count()).select_from(RoomRow))).scalar_one()
        habits = (await self.session.execute(select(func.count()).select_from(HabitRow))).scalar_one()
        return users, rooms, habits

    async def list_users(self) -> list[UserRow]:
        query = select(UserRow).order_by(UserRow.created_at.desc())
        return list((await self.session.execute(query)).scalars().all())

    async def list_rooms_with_owner(self) -> list[tuple[RoomRow, UserRow, int]]:
        member_count = (
            select(func.count())
            .where(RoomMemberRow.room_id == RoomRow.id)
            .scalar_subquery()
        )
        query = (
            select(RoomRow, UserRow, member_count)
            .join(UserRow, UserRow.id == RoomRow.owner_id)
            .order_by(RoomRow.created_at.desc())
        )
        return [(room, owner, count) for room, owner, count in (await self.session.execute(query)).all()]
