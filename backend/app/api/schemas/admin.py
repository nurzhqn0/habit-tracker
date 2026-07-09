from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.api.schemas.habits import HabitOverviewOut
from app.api.schemas.rooms import MemberOut, RoomHabitOut, RoomOut


class AdminStatsOut(BaseModel):
    total_users: int
    total_rooms: int
    total_habits: int


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    first_name: str
    photo_url: str | None
    bot_linked: bool
    created_at: datetime
    last_login_at: datetime | None

    @model_validator(mode="after")
    def _avatar_proxy_url(self) -> "AdminUserOut":
        self.photo_url = f"/api/v1/avatars/{self.id}"
        return self


class AdminUserDetailOut(BaseModel):
    user: AdminUserOut
    habits: list[HabitOverviewOut]


class AdminRoomListItemOut(BaseModel):
    room: RoomOut
    owner: AdminUserOut
    member_count: int


class AdminRoomDetailOut(BaseModel):
    room: RoomOut
    owner: AdminUserOut
    members: list[MemberOut]
    habits: list[RoomHabitOut]
