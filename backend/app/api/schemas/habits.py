from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HabitBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    question: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=2000)
    type: int = Field(default=0, ge=0, le=1)
    color: int = Field(default=8, ge=0, le=19)
    freq_num: int = Field(default=1, ge=1, le=366)
    freq_den: int = Field(default=1, ge=1, le=366)
    reminder_hour: int | None = Field(default=None, ge=0, le=23)
    reminder_min: int | None = Field(default=None, ge=0, le=59)
    reminder_days: int = Field(default=127, ge=0, le=127)
    target_type: int = Field(default=0, ge=0, le=1)
    target_value: float = Field(default=0.0, ge=0)
    unit: str = Field(default="", max_length=50)


class HabitCreate(HabitBase):
    pass


class HabitPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    question: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    color: int | None = Field(default=None, ge=0, le=19)
    freq_num: int | None = Field(default=None, ge=1, le=366)
    freq_den: int | None = Field(default=None, ge=1, le=366)
    reminder_hour: int | None = Field(default=None, ge=0, le=23)
    reminder_min: int | None = Field(default=None, ge=0, le=59)
    reminder_days: int | None = Field(default=None, ge=0, le=127)
    target_type: int | None = Field(default=None, ge=0, le=1)
    target_value: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=50)
    clear_reminder: bool = False


class HabitOut(HabitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    position: int
    created_at: datetime


class HabitOverviewOut(BaseModel):
    habit: HabitOut
    score: float
    streak: int
    entries: dict[date, int]
    notes: dict[date, str]


class ReorderRequest(BaseModel):
    ordered_ids: list[int]


class EntryUpsert(BaseModel):
    value: int
    notes: str | None = Field(default=None, max_length=2000)


class EntryChangeOut(BaseModel):
    value: int
    score: float
    streak: int
    entries: dict[date, int]


class EntryOut(BaseModel):
    date: date
    value: int
    notes: str
