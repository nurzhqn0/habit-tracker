from fastapi import APIRouter

from app.api.deps import CurrentUserDep, SessionDep
from app.api.schemas.auth import PreferencesOut, PreferencesPatch, UserOut
from app.infrastructure.repositories.user_repo import UserRepo

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUserDep) -> UserOut:
    return user


@router.get("/me/preferences", response_model=PreferencesOut)
async def get_preferences(user: CurrentUserDep, session: SessionDep) -> PreferencesOut:
    prefs = await UserRepo(session).get_or_create_preferences(user.id)
    await session.commit()
    return prefs


@router.patch("/me/preferences", response_model=PreferencesOut)
async def update_preferences(
    patch: PreferencesPatch, user: CurrentUserDep, session: SessionDep
) -> PreferencesOut:
    prefs = await UserRepo(session).get_or_create_preferences(user.id)
    for field, value in patch.model_dump(exclude_none=True).items():
        setattr(prefs, field, value)
    await session.commit()
    return prefs
