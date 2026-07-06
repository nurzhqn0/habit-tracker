import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.domain.errors import ForbiddenError
from app.infrastructure.db.tables import UserRow
from app.infrastructure.repositories.token_repo import TokenRepo
from app.infrastructure.repositories.user_repo import UserRepo
from app.infrastructure.security.jwt import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.infrastructure.telegram.oidc_verifier import verify_id_token


@dataclass
class AuthResult:
    user: UserRow
    access_token: str
    refresh_token: str


async def _issue_tokens(session: AsyncSession, user: UserRow, settings: Settings) -> AuthResult:
    refresh = generate_refresh_token()
    await TokenRepo(session).add(user.id, hash_refresh_token(refresh), settings.refresh_token_days)
    access = create_access_token(user.id, settings)
    return AuthResult(user=user, access_token=access, refresh_token=refresh)


async def telegram_login(session: AsyncSession, id_token: str, settings: Settings) -> AuthResult:
    # JWKS fetch inside is blocking urllib (cached after first call) — keep it off the loop.
    claims = await asyncio.to_thread(verify_id_token, id_token, settings.tg_client_id)
    if claims is None or not claims.get("id"):
        raise ForbiddenError("Invalid Telegram authentication data")

    users = UserRepo(session)
    user = await users.upsert_from_telegram(
        telegram_id=int(claims["id"]),
        first_name=str(claims.get("given_name") or claims.get("name") or ""),
        username=str(claims["preferred_username"]) if claims.get("preferred_username") else None,
        photo_url=str(claims["picture"]) if claims.get("picture") else None,
    )
    await users.get_or_create_preferences(user.id)
    result = await _issue_tokens(session, user, settings)
    await session.commit()
    return result


async def refresh_session(session: AsyncSession, refresh_token: str, settings: Settings) -> AuthResult:
    tokens = TokenRepo(session)
    row = await tokens.get_valid(hash_refresh_token(refresh_token))
    if row is None:
        raise ForbiddenError("Invalid refresh token")

    user = await UserRepo(session).get_by_id(row.user_id)
    if user is None:
        raise ForbiddenError("Invalid refresh token")

    # Rotation with a short grace window instead of instant revocation, so a
    # concurrent refresh from another tab (or the SSR/client race) still works.
    await tokens.retire(row)
    result = await _issue_tokens(session, user, settings)
    await session.commit()
    return result


async def logout(session: AsyncSession, refresh_token: str) -> None:
    tokens = TokenRepo(session)
    row = await tokens.get_valid(hash_refresh_token(refresh_token))
    if row is not None:
        await tokens.revoke(row)
        await session.commit()
