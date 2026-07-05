from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.tables import RefreshTokenRow


class TokenRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, token_hash: str, days_valid: int) -> RefreshTokenRow:
        row = RefreshTokenRow(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=days_valid),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_valid(self, token_hash: str) -> RefreshTokenRow | None:
        result = await self.session.execute(
            select(RefreshTokenRow).where(
                RefreshTokenRow.token_hash == token_hash,
                RefreshTokenRow.revoked.is_(False),
                RefreshTokenRow.expires_at > datetime.now(UTC).replace(tzinfo=None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, row: RefreshTokenRow) -> None:
        row.revoked = True
        await self.session.flush()
