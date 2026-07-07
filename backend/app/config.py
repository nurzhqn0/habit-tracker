from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "production"  # "production" enables strict startup guards
    database_url: str = "sqlite+aiosqlite:///./data/habitflow.db"
    jwt_secret: str = "dev-secret-change-me-in-production-0000"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    bot_token: str = ""
    bot_username: str = ""
    tg_client_id: str = ""  # BotFather -> Bot Settings -> Web Login -> Client ID
    tg_client_secret: str = ""  # Same page -> Client Secret (needed for the redirect code flow)

    frontend_origin: str = "http://localhost:3000"
    test_mode: bool = False

    @field_validator("frontend_origin")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
