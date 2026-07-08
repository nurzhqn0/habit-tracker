import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import NotFoundError
from app.infrastructure.db.tables import (
    ActivityEventRow,
    HabitLinkRow,
    RoomHabitRow,
    RoomMemberRow,
    RoomRow,
    UserRow,
)


def generate_invite_code() -> str:
    return secrets.token_urlsafe(6)


class RoomRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, owner_id: int, name: str, description: str) -> RoomRow:
        room = RoomRow(
            name=name, description=description, owner_id=owner_id, invite_code=generate_invite_code()
        )
        self.session.add(room)
        await self.session.flush()
        self.session.add(RoomMemberRow(room_id=room.id, user_id=owner_id, role="owner"))
        await self.session.flush()
        return room

    async def get(self, room_id: int) -> RoomRow:
        room = await self.session.get(RoomRow, room_id)
        if room is None:
            raise NotFoundError("Room not found")
        return room

    async def get_by_invite_code(self, code: str) -> RoomRow | None:
        result = await self.session.execute(select(RoomRow).where(RoomRow.invite_code == code))
        return result.scalar_one_or_none()

    async def rooms_for_user(self, user_id: int) -> list[RoomRow]:
        query = (
            select(RoomRow)
            .join(RoomMemberRow, RoomMemberRow.room_id == RoomRow.id)
            .where(RoomMemberRow.user_id == user_id)
            .order_by(RoomRow.id)
        )
        return list((await self.session.execute(query)).scalars())

    async def membership(self, room_id: int, user_id: int) -> RoomMemberRow | None:
        query = select(RoomMemberRow).where(
            RoomMemberRow.room_id == room_id, RoomMemberRow.user_id == user_id
        )
        return (await self.session.execute(query)).scalar_one_or_none()

    async def members_with_users(self, room_id: int) -> list[tuple[RoomMemberRow, UserRow]]:
        query = (
            select(RoomMemberRow, UserRow)
            .join(UserRow, UserRow.id == RoomMemberRow.user_id)
            .where(RoomMemberRow.room_id == room_id)
            .order_by(RoomMemberRow.joined_at)
        )
        return [(m, u) for m, u in (await self.session.execute(query)).all()]

    async def room_habits(self, room_id: int) -> list[RoomHabitRow]:
        query = select(RoomHabitRow).where(RoomHabitRow.room_id == room_id)
        return list((await self.session.execute(query)).scalars().all())

    async def get_room_habit(self, room_id: int, room_habit_id: int) -> RoomHabitRow:
        habit = await self.session.get(RoomHabitRow, room_habit_id)
        if habit is None or habit.room_id != room_id:
            raise NotFoundError("Room habit not found")
        return habit

    async def links_for_room_habits(self, room_habit_ids: list[int]) -> list[HabitLinkRow]:
        if not room_habit_ids:
            return []
        query = select(HabitLinkRow).where(HabitLinkRow.room_habit_id.in_(room_habit_ids))
        return list((await self.session.execute(query)).scalars().all())

    async def link_for_user(self, room_habit_id: int, user_id: int) -> HabitLinkRow | None:
        query = select(HabitLinkRow).where(
            HabitLinkRow.room_habit_id == room_habit_id, HabitLinkRow.user_id == user_id
        )
        return (await self.session.execute(query)).scalar_one_or_none()

    async def link_for_habit(self, habit_id: int) -> HabitLinkRow | None:
        query = select(HabitLinkRow).where(HabitLinkRow.habit_id == habit_id)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def add_event(
        self,
        room_id: int,
        user_id: int,
        type_: str,
        room_habit_id: int | None = None,
        entry_date=None,
        value: int | None = None,
    ) -> ActivityEventRow:
        event = ActivityEventRow(
            room_id=room_id,
            user_id=user_id,
            type=type_,
            room_habit_id=room_habit_id,
            entry_date=entry_date,
            value=value,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def feed(self, room_id: int, cursor: int | None, limit: int) -> list[ActivityEventRow]:
        query = select(ActivityEventRow).where(ActivityEventRow.room_id == room_id)
        if cursor is not None:
            query = query.where(ActivityEventRow.id < cursor)
        query = query.order_by(ActivityEventRow.id.desc()).limit(limit)
        return list((await self.session.execute(query)).scalars().all())
