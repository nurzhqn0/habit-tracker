"""Bot worker entrypoint: aiogram long polling + APScheduler reminder ticks.

Runs as a separate process from the API (shares the SQLite file via WAL):
    python -m app.workers.bot.main
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.infrastructure.db.base import create_engine, create_session_factory
from app.workers.bot import handlers
from app.workers.bot.scheduler import reminder_tick

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not configured")

    engine = create_engine()
    session_factory = create_session_factory(engine)
    handlers.session_factory = session_factory

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(handlers.router)

    # Persistent "Open app" button next to the message input.
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Open app", web_app=WebAppInfo(url=f"{settings.frontend_origin}/app")
        )
    )
    log.info("Menu button set with URL: %s/app", settings.frontend_origin)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(reminder_tick, "cron", second=0, args=[bot, session_factory])
    scheduler.start()

    log.info("Bot worker started (@%s)", settings.bot_username or "unknown")
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
