from pydantic import BaseModel, ConfigDict


class TelegramAuthPayload(BaseModel):
    model_config = ConfigDict(extra="allow")  # widget may add fields; all participate in HMAC

    id: int
    first_name: str = ""
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    first_name: str
    photo_url: str | None
    bot_linked: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: str
    show_question_marks: bool
    skip_days_enabled: bool
    first_weekday: int
    timezone: str
    reminders_enabled: bool
    room_notifications: bool


class PreferencesPatch(BaseModel):
    theme: str | None = None
    show_question_marks: bool | None = None
    skip_days_enabled: bool | None = None
    first_weekday: int | None = None
    timezone: str | None = None
    reminders_enabled: bool | None = None
    room_notifications: bool | None = None
