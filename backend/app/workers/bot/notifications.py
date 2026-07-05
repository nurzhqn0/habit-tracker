"""Tails activity_events and DMs room members about friends' completions."""

import logging

from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure.db.tables import (
    ActivityEventRow,
    RoomHabitRow,
    RoomMemberRow,
    RoomRow,
    UserPreferencesRow,
    UserRow,
)

log = logging.getLogger(__name__)

_last_seen_id: int | None = None

NOTIFIED_TYPES = {"entry_completed", "member_joined"}


async def notification_tick(bot: Bot, session_factory: async_sessionmaker) -> None:
    global _last_seen_id

    async with session_factory() as session:
        if _last_seen_id is None:
            # First tick: start from the current tail, don't replay history.
            _last_seen_id = (await session.scalar(select(func.max(ActivityEventRow.id)))) or 0
            return

        events = list(
            (
                await session.execute(
                    select(ActivityEventRow)
                    .where(ActivityEventRow.id > _last_seen_id, ActivityEventRow.type.in_(NOTIFIED_TYPES))
                    .order_by(ActivityEventRow.id)
                    .limit(200)
                )
            ).scalars()
        )
        max_id = await session.scalar(select(func.max(ActivityEventRow.id)))
        if not events:
            _last_seen_id = max_id or _last_seen_id
            return

        for event in events:
            actor = await session.get(UserRow, event.user_id)
            room = await session.get(RoomRow, event.room_id)
            if actor is None or room is None:
                continue
            habit_name = None
            if event.room_habit_id:
                habit = await session.get(RoomHabitRow, event.room_habit_id)
                habit_name = habit.name if habit else None

            if event.type == "entry_completed" and habit_name:
                text = f"🏆 {actor.first_name} completed *{habit_name}* in *{room.name}*"
            elif event.type == "member_joined":
                text = f"👋 {actor.first_name} joined *{room.name}*"
            else:
                continue

            recipients = (
                await session.execute(
                    select(UserRow)
                    .join(RoomMemberRow, RoomMemberRow.user_id == UserRow.id)
                    .join(UserPreferencesRow, UserPreferencesRow.user_id == UserRow.id)
                    .where(
                        RoomMemberRow.room_id == event.room_id,
                        UserRow.id != event.user_id,
                        UserRow.bot_linked.is_(True),
                        UserPreferencesRow.room_notifications.is_(True),
                    )
                )
            ).scalars()

            for recipient in recipients:
                try:
                    await bot.send_message(recipient.telegram_id, text, parse_mode="Markdown")
                except Exception:  # noqa: BLE001
                    log.warning("Failed to notify %s", recipient.telegram_id, exc_info=True)

        _last_seen_id = max(events[-1].id, max_id or 0)
