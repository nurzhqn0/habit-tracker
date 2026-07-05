from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep, SettingsDep
from app.api.schemas.rooms import (
    FeedEventOut,
    JoinRequest,
    LeaderboardRowOut,
    LinkRequest,
    MemberOut,
    RoomCreate,
    RoomHabitCreate,
    RoomHabitOut,
    RoomHabitPatch,
    RoomHabitWithLinkOut,
    RoomOut,
    RoomPatch,
)
from app.application.use_cases import rooms as rooms_uc
from app.infrastructure.db.tables import RoomHabitRow, UserRow
from app.infrastructure.repositories.room_repo import RoomRepo

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomOut, status_code=201)
async def create_room(body: RoomCreate, user: CurrentUserDep, session: SessionDep) -> RoomOut:
    return await rooms_uc.create_room(session, user.id, body.name, body.description)


@router.get("", response_model=list[RoomOut])
async def my_rooms(user: CurrentUserDep, session: SessionDep) -> list[RoomOut]:
    return await RoomRepo(session).rooms_for_user(user.id)


@router.post("/join", response_model=RoomOut)
async def join(body: JoinRequest, user: CurrentUserDep, session: SessionDep) -> RoomOut:
    return await rooms_uc.join_room(session, user.id, body.code)


@router.get("/{room_id}", response_model=RoomOut)
async def get_room(room_id: int, user: CurrentUserDep, session: SessionDep) -> RoomOut:
    return await rooms_uc._require_member(session, room_id, user.id)


@router.patch("/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: int, body: RoomPatch, user: CurrentUserDep, session: SessionDep
) -> RoomOut:
    return await rooms_uc.update_room(session, user.id, room_id, body.model_dump())


@router.delete("/{room_id}", status_code=204)
async def delete_room(room_id: int, user: CurrentUserDep, session: SessionDep) -> None:
    await rooms_uc.delete_room(session, user.id, room_id)


@router.post("/{room_id}/invite/rotate")
async def rotate_invite(
    room_id: int, user: CurrentUserDep, session: SessionDep, settings: SettingsDep
) -> dict:
    code = await rooms_uc.rotate_invite(session, user.id, room_id)
    return {"invite_code": code, "link": f"{settings.frontend_origin}/app/rooms/join/{code}"}


@router.get("/{room_id}/members", response_model=list[MemberOut])
async def members(room_id: int, user: CurrentUserDep, session: SessionDep) -> list[MemberOut]:
    await rooms_uc._require_member(session, room_id, user.id)
    return [
        MemberOut(
            user_id=u.id, first_name=u.first_name, username=u.username,
            photo_url=u.photo_url, role=m.role, joined_at=m.joined_at,
        )
        for m, u in await RoomRepo(session).members_with_users(room_id)
    ]


@router.delete("/{room_id}/members/{target_user_id}", status_code=204)
async def remove_member(
    room_id: int, target_user_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    await rooms_uc.remove_member(session, user.id, room_id, target_user_id)


@router.post("/{room_id}/habits", response_model=RoomHabitOut, status_code=201)
async def create_room_habit(
    room_id: int, body: RoomHabitCreate, user: CurrentUserDep, session: SessionDep
) -> RoomHabitOut:
    return await rooms_uc.create_room_habit(session, user.id, room_id, body.model_dump())


@router.get("/{room_id}/habits", response_model=list[RoomHabitWithLinkOut])
async def room_habits(
    room_id: int, user: CurrentUserDep, session: SessionDep
) -> list[RoomHabitWithLinkOut]:
    await rooms_uc._require_member(session, room_id, user.id)
    repo = RoomRepo(session)
    habits = await repo.room_habits(room_id)
    links = await repo.links_for_room_habits([h.id for h in habits])
    return [
        RoomHabitWithLinkOut(
            habit=RoomHabitOut.model_validate(h),
            linked_habit_id=next(
                (link.habit_id for link in links if link.room_habit_id == h.id and link.user_id == user.id),
                None,
            ),
            members_linked=sum(1 for link in links if link.room_habit_id == h.id),
        )
        for h in habits
    ]


@router.patch("/{room_id}/habits/{room_habit_id}", response_model=RoomHabitOut)
async def update_room_habit(
    room_id: int, room_habit_id: int, body: RoomHabitPatch, user: CurrentUserDep, session: SessionDep
) -> RoomHabitOut:
    return await rooms_uc.update_room_habit(
        session, user.id, room_id, room_habit_id, body.model_dump(exclude_none=True)
    )


@router.delete("/{room_id}/habits/{room_habit_id}", status_code=204)
async def delete_room_habit(
    room_id: int, room_habit_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    await rooms_uc.delete_room_habit(session, user.id, room_id, room_habit_id)


@router.post("/{room_id}/habits/{room_habit_id}/link")
async def link_habit(
    room_id: int, room_habit_id: int, body: LinkRequest, user: CurrentUserDep, session: SessionDep
) -> dict:
    habit = await rooms_uc.link_habit(session, user.id, room_id, room_habit_id, body.habit_id)
    return {"habit_id": habit.id}


@router.delete("/{room_id}/habits/{room_habit_id}/link", status_code=204)
async def unlink_habit(
    room_id: int, room_habit_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    await rooms_uc.unlink_habit(session, user.id, room_id, room_habit_id)


@router.get("/{room_id}/leaderboard", response_model=list[LeaderboardRowOut])
async def leaderboard(
    room_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    period: Literal["week", "month", "all"] = "week",
) -> list[LeaderboardRowOut]:
    rows = await rooms_uc.leaderboard(session, user.id, room_id, period)
    return [LeaderboardRowOut(**row.__dict__) for row in rows]


@router.get("/{room_id}/feed", response_model=list[FeedEventOut])
async def feed(
    room_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    cursor: int | None = None,
    limit: int = Query(default=30, le=100),
) -> list[FeedEventOut]:
    await rooms_uc._require_member(session, room_id, user.id)
    events = await RoomRepo(session).feed(room_id, cursor, limit)

    user_ids = {e.user_id for e in events}
    habit_ids = {e.room_habit_id for e in events if e.room_habit_id}
    users = {
        u.id: u
        for u in (await session.execute(select(UserRow).where(UserRow.id.in_(user_ids)))).scalars()
    } if user_ids else {}
    habits = {
        h.id: h
        for h in (
            await session.execute(select(RoomHabitRow).where(RoomHabitRow.id.in_(habit_ids)))
        ).scalars()
    } if habit_ids else {}

    return [
        FeedEventOut(
            id=e.id,
            user_id=e.user_id,
            first_name=users[e.user_id].first_name if e.user_id in users else "Unknown",
            photo_url=users[e.user_id].photo_url if e.user_id in users else None,
            type=e.type,
            room_habit_id=e.room_habit_id,
            room_habit_name=habits[e.room_habit_id].name if e.room_habit_id in habits else None,
            entry_date=e.entry_date,
            value=e.value,
            created_at=e.created_at,
        )
        for e in events
    ]
