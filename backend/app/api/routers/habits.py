from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.api.schemas.habits import (
    EntryChangeOut,
    EntryOut,
    EntryUpsert,
    HabitCreate,
    HabitOut,
    HabitOverviewOut,
    HabitPatch,
    ReorderRequest,
)
from app.application.use_cases import entries as entries_uc
from app.application.use_cases import habits as habits_uc
from app.infrastructure.repositories.habit_repo import HabitRepo

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("", response_model=list[HabitOut])
async def list_habits(user: CurrentUserDep, session: SessionDep) -> list[HabitOut]:
    return await HabitRepo(session).list_for_user(user.id)


@router.get("/overview", response_model=list[HabitOverviewOut])
async def overview(
    user: CurrentUserDep,
    session: SessionDep,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    sort: Literal["manual", "name", "color", "score", "status"] = "manual",
) -> list[HabitOverviewOut]:
    items = await habits_uc.get_overview(session, user.id, from_date, to_date, sort)
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


@router.post("", response_model=HabitOut, status_code=201)
async def create_habit(body: HabitCreate, user: CurrentUserDep, session: SessionDep) -> HabitOut:
    return await habits_uc.create_habit(session, user.id, body.model_dump())


@router.get("/{habit_id}", response_model=HabitOut)
async def get_habit(habit_id: int, user: CurrentUserDep, session: SessionDep) -> HabitOut:
    return await HabitRepo(session).get_owned(habit_id, user.id)


@router.patch("/{habit_id}", response_model=HabitOut)
async def update_habit(
    habit_id: int, body: HabitPatch, user: CurrentUserDep, session: SessionDep
) -> HabitOut:
    fields = body.model_dump(exclude_none=True, exclude={"clear_reminder"})
    if body.clear_reminder:
        fields["reminder_hour"] = None
        fields["reminder_min"] = None
    return await habits_uc.update_habit(session, user.id, habit_id, fields)


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(habit_id: int, user: CurrentUserDep, session: SessionDep) -> None:
    await habits_uc.delete_habit(session, user.id, habit_id)


@router.put("/positions", status_code=204)
async def reorder(body: ReorderRequest, user: CurrentUserDep, session: SessionDep) -> None:
    await habits_uc.reorder_habits(session, user.id, body.ordered_ids)


@router.get("/{habit_id}/entries", response_model=list[EntryOut])
async def get_entries(
    habit_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
) -> list[EntryOut]:
    computed = await entries_uc.get_computed_entries(session, user.id, habit_id, from_date, to_date)
    return [
        EntryOut(date=d, value=value, notes=notes)
        for d, (value, notes) in sorted(computed.items(), reverse=True)
    ]


@router.put("/{habit_id}/entries/{entry_date}", response_model=EntryChangeOut)
async def upsert_entry(
    habit_id: int, entry_date: date, body: EntryUpsert, user: CurrentUserDep, session: SessionDep
) -> EntryChangeOut:
    change = await entries_uc.upsert_entry(session, user.id, habit_id, entry_date, body.value, body.notes)
    return EntryChangeOut(**change.__dict__)


@router.post("/{habit_id}/entries/{entry_date}/toggle", response_model=EntryChangeOut)
async def toggle_entry(
    habit_id: int, entry_date: date, user: CurrentUserDep, session: SessionDep
) -> EntryChangeOut:
    change = await entries_uc.toggle_entry(session, user.id, habit_id, entry_date)
    return EntryChangeOut(**change.__dict__)


@router.delete("/{habit_id}/entries/{entry_date}", response_model=EntryChangeOut)
async def delete_entry(
    habit_id: int, entry_date: date, user: CurrentUserDep, session: SessionDep
) -> EntryChangeOut:
    change = await entries_uc.delete_entry(session, user.id, habit_id, entry_date)
    return EntryChangeOut(**change.__dict__)
