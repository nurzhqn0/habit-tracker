"""Minute tick: send due reminders (+ snoozed re-sends), dedupe within the day."""

import logging
from datetime import UTC, date as Date, datetime

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure.db.tables import HabitRow
from app.workers.bot import handlers
from app.workers.bot.reminders import DueReminder, find_due_reminders

log = logging.getLogger(__name__)

# (telegram_id, habit_id, iso_date) already sent — cleared when the date rolls over.
_sent: set[tuple[int, int, str]] = set()
_sent_day: str = ""


def _keyboard(reminder: DueReminder) -> InlineKeyboardMarkup:
    prefix = f"e:{reminder.habit_id}:{reminder.local_date.isoformat()}"
    buttons = [InlineKeyboardButton(text="✅ Done", callback_data=f"{prefix}:done")]
    if not reminder.is_numerical:
        buttons.append(InlineKeyboardButton(text="⏭ Skip", callback_data=f"{prefix}:skip"))
    buttons.append(InlineKeyboardButton(text="🕐 Later", callback_data=f"{prefix}:later"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


async def _send(bot: Bot, reminder: DueReminder) -> None:
    key = (reminder.telegram_id, reminder.habit_id, reminder.local_date.isoformat())
    if key in _sent:
        return
    text = reminder.question or f"Time for: {reminder.habit_name}"
    try:
        await bot.send_message(reminder.telegram_id, f"🔔 {text}", reply_markup=_keyboard(reminder))
        _sent.add(key)
    except Exception:  # noqa: BLE001 — user may have blocked the bot; never crash the tick
        log.warning("Failed to send reminder to %s", reminder.telegram_id, exc_info=True)


async def _resend_snoozed(bot: Bot, session_factory: async_sessionmaker) -> None:
    for key in list(handlers.snoozed):
        handlers.snoozed[key] -= 1
        if handlers.snoozed[key] > 0:
            continue
        del handlers.snoozed[key]
        telegram_id, habit_id, date_raw = key

        async with session_factory() as session:
            habit = (
                await session.execute(select(HabitRow).where(HabitRow.id == habit_id))
            ).scalar_one_or_none()
        if habit is None:
            continue

        _sent.discard((telegram_id, habit_id, date_raw))
        await _send(
            bot,
            DueReminder(
                telegram_id=telegram_id,
                user_id=habit.user_id,
                habit_id=habit_id,
                habit_name=habit.name,
                question=habit.question,
                is_numerical=habit.type == 1,
                local_date=Date.fromisoformat(date_raw),
            ),
        )


async def reminder_tick(bot: Bot, session_factory: async_sessionmaker) -> None:
    global _sent_day
    now_utc = datetime.now(UTC)

    today = now_utc.date().isoformat()
    if today != _sent_day:
        _sent.clear()
        _sent_day = today

    async with session_factory() as session:
        due = await find_due_reminders(session, now_utc)
    for reminder in due:
        await _send(bot, reminder)

    await _resend_snoozed(bot, session_factory)
