"""aiogram handlers: /start account linking + inline Done/Skip/Later callbacks."""

from datetime import date as Date

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.application.use_cases import entries as entries_uc
from app.config import get_settings
from app.domain.errors import DomainError
from app.domain.models.entry import SKIP, YES_MANUAL
from app.domain.models.habit import HabitType
from app.infrastructure.db.tables import UserRow
from app.infrastructure.repositories.habit_repo import HabitRepo

router = Router()

# Filled by main.py at startup.
session_factory: async_sessionmaker | None = None

# (telegram_id, habit_id, iso_date) snoozed until minute-of-day; consumed by scheduler.
snoozed: dict[tuple[int, int, str], int] = {}

SNOOZE_MINUTES = 60


async def _user_by_telegram(session, telegram_id: int) -> UserRow | None:
    result = await session.execute(select(UserRow).where(UserRow.telegram_id == telegram_id))
    return result.scalar_one_or_none()


def done_value(habit) -> int:
    """Entry value for a bot "Done" tap. Numerical entries are stored as value*1000."""
    if habit.type == HabitType.NUMERICAL:
        return int(habit.target_value * 1000)
    return YES_MANUAL


def _open_app_keyboard() -> InlineKeyboardMarkup | None:
    """An 'Open app' Mini App button. Telegram only accepts https web_app URLs,
    so it is omitted in local (http) dev."""
    origin = get_settings().frontend_origin
    if not origin.startswith("https://"):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📲 Open app", web_app=WebAppInfo(url=f"{origin}/app"))]
        ]
    )


@router.message(CommandStart())
async def on_start(message: Message) -> None:
    assert session_factory is not None
    async with session_factory() as session:
        user = await _user_by_telegram(session, message.from_user.id)
        if user is None:
            await message.answer(
                "I don't recognize this Telegram account yet.\n"
                "Log in on the website first, then tap Connect bot in Settings."
            )
            return
        user.bot_linked = True
        await session.commit()
    await message.answer(
        f"Connected! 🎉 Hi {message.from_user.first_name} — I'll send your habit reminders here.",
        reply_markup=_open_app_keyboard(),
    )


@router.callback_query(F.data.startswith("e:"))
async def on_entry_action(callback: CallbackQuery) -> None:
    assert session_factory is not None
    try:
        _, habit_id_raw, date_raw, action = (callback.data or "").split(":")
        habit_id = int(habit_id_raw)
        entry_date = Date.fromisoformat(date_raw)
    except ValueError:
        await callback.answer("Invalid action")
        return

    async with session_factory() as session:
        user = await _user_by_telegram(session, callback.from_user.id)
        if user is None:
            await callback.answer("Account not linked")
            return

        if action == "later":
            snoozed[(callback.from_user.id, habit_id, date_raw)] = SNOOZE_MINUTES
            await callback.answer(f"Okay — I'll remind you in {SNOOZE_MINUTES} minutes")
            if callback.message:
                await callback.message.edit_reply_markup(reply_markup=None)
            return

        try:
            habit = await HabitRepo(session).get_owned(habit_id, user.id)
            value = done_value(habit) if action == "done" else SKIP
            await entries_uc.upsert_entry(session, user.id, habit_id, entry_date, value, None)
        except DomainError:
            await callback.answer("Habit not found")
            return

    await callback.answer("Saved ✅" if action == "done" else "Skipped ⏭")
    if callback.message:
        suffix = "✅ Done" if action == "done" else "⏭ Skipped"
        await callback.message.edit_text(f"{callback.message.text}\n\n{suffix}")
