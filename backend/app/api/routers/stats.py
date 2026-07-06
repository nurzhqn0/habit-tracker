from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.application.use_cases import stats as stats_uc

router = APIRouter(prefix="/habits/{habit_id}/stats", tags=["stats"])

Bucket = Literal["day", "week", "month", "quarter", "year"]


@router.get("/overview")
async def overview(habit_id: int, user: CurrentUserDep, session: SessionDep) -> dict:
    return await stats_uc.overview(session, user.id, habit_id)


@router.get("/scores")
async def scores(
    habit_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    bucket: Bucket = "day",
    from_date: date | None = Query(default=None, alias="from"),
) -> list[dict]:
    return await stats_uc.scores_series(session, user.id, habit_id, bucket, from_date)


@router.get("/history")
async def history(
    habit_id: int, user: CurrentUserDep, session: SessionDep, year: int | None = None
) -> dict:
    return await stats_uc.history(session, user.id, habit_id, year)


@router.get("/bar")
async def bar(
    habit_id: int, user: CurrentUserDep, session: SessionDep, bucket: Bucket = "week"
) -> list[dict]:
    return await stats_uc.bar(session, user.id, habit_id, bucket)


@router.get("/weekdays")
async def weekdays(habit_id: int, user: CurrentUserDep, session: SessionDep) -> list[dict]:
    return await stats_uc.weekdays(session, user.id, habit_id)


@router.get("/frequency")
async def frequency(habit_id: int, user: CurrentUserDep, session: SessionDep) -> list[dict]:
    return await stats_uc.frequency(session, user.id, habit_id)


@router.get("/streaks")
async def streaks(
    habit_id: int, user: CurrentUserDep, session: SessionDep, limit: int = Query(default=10, le=50)
) -> list[dict]:
    return await stats_uc.streaks(session, user.id, habit_id, limit)


@router.get("/target")
async def target(habit_id: int, user: CurrentUserDep, session: SessionDep) -> list[dict]:
    return await stats_uc.target(session, user.id, habit_id)


@router.get("/notes")
async def notes(habit_id: int, user: CurrentUserDep, session: SessionDep) -> list[dict]:
    return await stats_uc.notes(session, user.id, habit_id)
