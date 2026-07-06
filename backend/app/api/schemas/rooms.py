from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class RoomPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    owner_id: int
    invite_code: str
    created_at: datetime


class JoinRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class MemberOut(BaseModel):
    user_id: int
    first_name: str
    username: str | None
    photo_url: str | None
    role: str
    joined_at: datetime


class MemberRolePatch(BaseModel):
    role: Literal["admin", "member"]


class InviteByUsernameRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class InviteByUsernameOut(BaseModel):
    status: Literal["sent", "not_linked", "not_registered", "already_member"]
    username: str
    link: str


class TransferRequest(BaseModel):
    user_id: int


class RoomHabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    type: int = Field(default=0, ge=0, le=1)
    color: int = Field(default=8, ge=0, le=19)
    freq_num: int = Field(default=1, ge=1, le=366)
    freq_den: int = Field(default=1, ge=1, le=366)
    target_type: int = Field(default=0, ge=0, le=1)
    target_value: float = Field(default=0.0, ge=0)
    unit: str = Field(default="", max_length=50)


class RoomHabitPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    color: int | None = Field(default=None, ge=0, le=19)
    freq_num: int | None = Field(default=None, ge=1, le=366)
    freq_den: int | None = Field(default=None, ge=1, le=366)
    target_type: int | None = Field(default=None, ge=0, le=1)
    target_value: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=50)
    archived: bool | None = None


class RoomHabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    created_by: int
    name: str
    description: str
    type: int
    color: int
    freq_num: int
    freq_den: int
    target_type: int
    target_value: float
    unit: str
    archived: bool


class RoomHabitWithLinkOut(BaseModel):
    habit: RoomHabitOut
    linked_habit_id: int | None
    members_linked: int


class LinkRequest(BaseModel):
    habit_id: int | None = None


class LeaderboardRowOut(BaseModel):
    user_id: int
    first_name: str
    username: str | None
    photo_url: str | None
    score: float
    streak: int
    completions: int
    linked_habits: int


class FeedEventOut(BaseModel):
    id: int
    user_id: int
    first_name: str
    photo_url: str | None
    type: str
    room_habit_id: int | None
    room_habit_name: str | None
    entry_date: date | None
    value: int | None
    created_at: datetime
