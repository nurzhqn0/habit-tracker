from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, get_admin_user
from app.api.schemas.admin import (
    AdminRoomDetailOut,
    AdminRoomListItemOut,
    AdminStatsOut,
    AdminUserDetailOut,
    AdminUserOut,
)
from app.api.schemas.habits import HabitOut, HabitOverviewOut
from app.api.schemas.rooms import MemberOut, RoomHabitOut, RoomOut
from app.application.use_cases import habits as habits_uc
from app.application.use_cases import stats as stats_uc
from app.domain.errors import NotFoundError
from app.infrastructure.repositories.admin_repo import AdminRepo
from app.infrastructure.repositories.habit_repo import HabitRepo
from app.infrastructure.repositories.room_repo import RoomRepo
from app.infrastructure.repositories.user_repo import UserRepo

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])

Bucket = Literal["day", "week", "month", "quarter", "year"]


@router.get("/stats", response_model=AdminStatsOut)
async def stats(session: SessionDep) -> AdminStatsOut:
    users, rooms, habits = await AdminRepo(session).counts()
    return AdminStatsOut(total_users=users, total_rooms=rooms, total_habits=habits)


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(session: SessionDep) -> list[AdminUserOut]:
    rows = await AdminRepo(session).list_users()
    return [AdminUserOut.model_validate(u) for u in rows]


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
async def user_detail(
    user_id: int,
    session: SessionDep,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
) -> AdminUserDetailOut:
    target = await UserRepo(session).get_by_id(user_id)
    if target is None:
        raise NotFoundError("User not found")
    items = await habits_uc.get_overview(session, user_id, from_date, to_date)
    return AdminUserDetailOut(
        user=AdminUserOut.model_validate(target),
        habits=[
            HabitOverviewOut(
                habit=HabitOut.model_validate(i.habit),
                score=i.score,
                streak=i.streak,
                entries=i.entries,
                notes=i.notes,
            )
            for i in items
        ],
    )


# Read-only detail view of one habit of any user — mirrors the member-view
# habit endpoints (member_stats.py) but without a room-membership gate or
# join-date history floor. stats_uc validates ownership via get_owned (404).
habit_router = APIRouter(prefix="/users/{user_id}/habits/{habit_id}")


@habit_router.get("", response_model=HabitOut)
async def user_habit(user_id: int, habit_id: int, session: SessionDep) -> HabitOut:
    return await HabitRepo(session).get_owned(habit_id, user_id)


@habit_router.get("/stats/overview")
async def habit_overview(user_id: int, habit_id: int, session: SessionDep) -> dict:
    return await stats_uc.overview(session, user_id, habit_id)


@habit_router.get("/stats/scores")
async def habit_scores(
    user_id: int,
    habit_id: int,
    session: SessionDep,
    bucket: Bucket = "day",
    from_date: date | None = Query(default=None, alias="from"),
) -> list[dict]:
    return await stats_uc.scores_series(session, user_id, habit_id, bucket, from_date)


@habit_router.get("/stats/history")
async def habit_history(
    user_id: int, habit_id: int, session: SessionDep, year: int | None = None
) -> dict:
    return await stats_uc.history(session, user_id, habit_id, year)


@habit_router.get("/stats/bar")
async def habit_bar(
    user_id: int, habit_id: int, session: SessionDep, bucket: Bucket = "week"
) -> list[dict]:
    return await stats_uc.bar(session, user_id, habit_id, bucket)


@habit_router.get("/stats/weekdays")
async def habit_weekdays(user_id: int, habit_id: int, session: SessionDep) -> list[dict]:
    return await stats_uc.weekdays(session, user_id, habit_id)


@habit_router.get("/stats/frequency")
async def habit_frequency(user_id: int, habit_id: int, session: SessionDep) -> list[dict]:
    return await stats_uc.frequency(session, user_id, habit_id)


@habit_router.get("/stats/streaks")
async def habit_streaks(
    user_id: int, habit_id: int, session: SessionDep, limit: int = Query(default=10, le=50)
) -> list[dict]:
    return await stats_uc.streaks(session, user_id, habit_id, limit)


@habit_router.get("/stats/target")
async def habit_target(user_id: int, habit_id: int, session: SessionDep) -> list[dict]:
    return await stats_uc.target(session, user_id, habit_id)


@habit_router.get("/stats/notes")
async def habit_notes(user_id: int, habit_id: int, session: SessionDep) -> list[dict]:
    return await stats_uc.notes(session, user_id, habit_id)


router.include_router(habit_router)


@router.get("/rooms", response_model=list[AdminRoomListItemOut])
async def list_rooms(session: SessionDep) -> list[AdminRoomListItemOut]:
    rows = await AdminRepo(session).list_rooms_with_owner()
    return [
        AdminRoomListItemOut(
            room=RoomOut.model_validate(room),
            owner=AdminUserOut.model_validate(owner),
            member_count=count,
        )
        for room, owner, count in rows
    ]


@router.get("/rooms/{room_id}", response_model=AdminRoomDetailOut)
async def room_detail(room_id: int, session: SessionDep) -> AdminRoomDetailOut:
    repo = RoomRepo(session)
    room = await repo.get(room_id)
    owner = await UserRepo(session).get_by_id(room.owner_id)
    members = await repo.members_with_users(room_id)
    habits = await repo.room_habits(room_id)
    return AdminRoomDetailOut(
        room=RoomOut.model_validate(room),
        owner=AdminUserOut.model_validate(owner),
        members=[
            MemberOut(
                user_id=u.id, first_name=u.first_name, username=u.username,
                photo_url=f"/api/v1/avatars/{u.id}", role=m.role, joined_at=m.joined_at,
            )
            for m, u in members
        ],
        habits=[RoomHabitOut.model_validate(h) for h in habits],
    )
