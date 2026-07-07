from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routers import auth, avatars, export, habits, me, member_stats, rooms, stats
from app.config import get_settings
from app.infrastructure.db.base import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_engine()
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.bot = Bot(token=settings.bot_token) if settings.bot_token else None
    yield
    if app.state.bot is not None:
        await app.state.bot.session.close()
    await engine.dispose()


_DEV_JWT_SECRET = "dev-secret-change-me-in-production-0000"


def _enforce_production_settings(settings) -> None:
    if settings.environment != "production":
        return
    if settings.jwt_secret == _DEV_JWT_SECRET or len(settings.jwt_secret) < 32:
        raise RuntimeError("Production requires a JWT_SECRET of at least 32 characters")
    if settings.test_mode:
        raise RuntimeError("TEST_MODE must be disabled in production")


def create_app() -> FastAPI:
    settings = get_settings()
    _enforce_production_settings(settings)
    is_production = settings.environment == "production"
    app = FastAPI(
        title="HabitFlow API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler

    from app.api.routers.auth import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    register_error_handlers(app)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(me.router, prefix="/api/v1")
    app.include_router(habits.router, prefix="/api/v1")
    app.include_router(stats.router, prefix="/api/v1")
    app.include_router(export.router, prefix="/api/v1")
    app.include_router(rooms.router, prefix="/api/v1")
    app.include_router(member_stats.router, prefix="/api/v1")
    app.include_router(avatars.router, prefix="/api/v1")

    return app


app = create_app()
