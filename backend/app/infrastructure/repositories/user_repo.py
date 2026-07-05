from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.tables import UserPreferencesRow, UserRow


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> UserRow | None:
        return await self.session.get(UserRow, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> UserRow | None:
        result = await self.session.execute(select(UserRow).where(UserRow.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def upsert_from_telegram(
        self, telegram_id: int, first_name: str, username: str | None, photo_url: str | None
    ) -> UserRow:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = UserRow(telegram_id=telegram_id)
            self.session.add(user)
        user.first_name = first_name
        user.username = username
        user.photo_url = photo_url
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        return user

    async def get_or_create_preferences(self, user_id: int) -> UserPreferencesRow:
        prefs = await self.session.get(UserPreferencesRow, user_id)
        if prefs is None:
            prefs = UserPreferencesRow(user_id=user_id)
            self.session.add(prefs)
            await self.session.flush()
        return prefs
