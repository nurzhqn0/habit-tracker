from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import SessionDep, SettingsDep
from app.api.schemas.auth import RefreshRequest, TelegramLoginRequest, TokenResponse
from app.application.use_cases import auth as auth_uc
from app.infrastructure.repositories.user_repo import UserRepo

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/telegram", response_model=TokenResponse)
@limiter.limit("10/minute")
async def telegram_login(
    request: Request, payload: TelegramLoginRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    result = await auth_uc.telegram_login(session, payload.id_token, settings)
    return TokenResponse(
        access_token=result.access_token, refresh_token=result.refresh_token, user=result.user
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request, body: RefreshRequest, session: SessionDep, settings: SettingsDep
) -> TokenResponse:
    result = await auth_uc.refresh_session(session, body.refresh_token, settings)
    return TokenResponse(
        access_token=result.access_token, refresh_token=result.refresh_token, user=result.user
    )


@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, session: SessionDep) -> None:
    await auth_uc.logout(session, body.refresh_token)


@router.post("/test-login", response_model=TokenResponse)
async def test_login(session: SessionDep, settings: SettingsDep) -> TokenResponse:
    """E2E-test backdoor. Only mounted behavior when TEST_MODE=1; rejected otherwise."""
    if not settings.test_mode:
        raise HTTPException(status_code=404, detail="Not found")
    users = UserRepo(session)
    user = await users.upsert_from_telegram(
        telegram_id=999_000_001, first_name="Test User", username="testuser", photo_url=None
    )
    await users.get_or_create_preferences(user.id)
    result = await auth_uc._issue_tokens(session, user, settings)
    await session.commit()
    return TokenResponse(
        access_token=result.access_token, refresh_token=result.refresh_token, user=result.user
    )
