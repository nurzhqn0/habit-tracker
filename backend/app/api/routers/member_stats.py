from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.api.schemas.habits import HabitOut, HabitOverviewOut
from app.application.use_cases import rooms as rooms_uc
from app.application.use_cases import stats as stats_uc
from app.infrastructure.repositories.habit_repo import HabitRepo
from app.infrastructure.repositories.room_repo import RoomRepo

router = APIRouter(prefix="/rooms/{room_id}/members/{member_id}", tags=["member-view"])

Bucket = Literal["day", "week", "month", "quarter", "year"]


@router.get("/overview", response_model=list[HabitOverviewOut])
async def member_overview(
    room_id: int,
    member_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
) -> list[HabitOverviewOut]:
    items = await rooms_uc.member_overview(session, user.id, room_id, member_id, from_date, to_date)
    return [
        HabitOverviewOut(
            habit=HabitOut.model_validate(i.habit),
            score=i.score,
            streak=i.streak,
            entries=i.entries,
            notes=i.notes,
        )
        for i in items
    ]


async def _member_since(
    room_id: int, member_id: int, habit_id: int, user: CurrentUserDep, session: SessionDep
) -> date:
    """Authorizes admin access and returns the member's join date (history floor)."""
    await rooms_uc.authorize_member_habit(session, user.id, room_id, member_id, habit_id)
    membership = await RoomRepo(session).membership(room_id, member_id)
    return membership.joined_at.date()


habit_router = APIRouter(prefix="/habits/{habit_id}")

SinceDep = Depends(_member_since)


@habit_router.get("", response_model=HabitOut)
async def member_habit(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> HabitOut:
    return await HabitRepo(session).get_owned(habit_id, member_id)


@habit_router.get("/stats/overview")
async def overview(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> dict:
    return await stats_uc.overview(session, member_id, habit_id, since=since)


@habit_router.get("/stats/scores")
async def scores(
    habit_id: int,
    member_id: int,
    session: SessionDep,
    bucket: Bucket = "day",
    from_date: date | None = Query(default=None, alias="from"),
    since: date = SinceDep,
) -> list[dict]:
    return await stats_uc.scores_series(session, member_id, habit_id, bucket, from_date, since=since)


@habit_router.get("/stats/history")
async def history(
    habit_id: int, member_id: int, session: SessionDep, year: int | None = None, since: date = SinceDep
) -> dict:
    return await stats_uc.history(session, member_id, habit_id, year, since=since)


@habit_router.get("/stats/bar")
async def bar(
    habit_id: int, member_id: int, session: SessionDep, bucket: Bucket = "week", since: date = SinceDep
) -> list[dict]:
    return await stats_uc.bar(session, member_id, habit_id, bucket, since=since)


@habit_router.get("/stats/weekdays")
async def weekdays(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> list[dict]:
    return await stats_uc.weekdays(session, member_id, habit_id, since=since)


@habit_router.get("/stats/frequency")
async def frequency(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> list[dict]:
    return await stats_uc.frequency(session, member_id, habit_id, since=since)


@habit_router.get("/stats/streaks")
async def streaks(
    habit_id: int,
    member_id: int,
    session: SessionDep,
    limit: int = Query(default=10, le=50),
    since: date = SinceDep,
) -> list[dict]:
    return await stats_uc.streaks(session, member_id, habit_id, limit, since=since)


@habit_router.get("/stats/target")
async def target(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> list[dict]:
    return await stats_uc.target(session, member_id, habit_id, since=since)


@habit_router.get("/stats/notes")
async def notes(
    habit_id: int, member_id: int, session: SessionDep, since: date = SinceDep
) -> list[dict]:
    return await stats_uc.notes(session, member_id, habit_id, since=since)


router.include_router(habit_router)
