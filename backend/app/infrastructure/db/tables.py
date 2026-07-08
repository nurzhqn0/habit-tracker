from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_name: Mapped[str] = mapped_column(Text, default="")
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bot_linked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserPreferencesRow(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme: Mapped[str] = mapped_column(Text, default="system")
    show_question_marks: Mapped[bool] = mapped_column(Boolean, default=False)
    skip_days_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    first_weekday: Mapped[int] = mapped_column(Integer, default=0)
    timezone: Mapped[str] = mapped_column(Text, default="UTC")
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    room_notifications: Mapped[bool] = mapped_column(Boolean, default=True)


class RefreshTokenRow(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class HabitRow(Base):
    __tablename__ = "habits"
    __table_args__ = (Index("ix_habits_user_position", "user_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    uuid: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    question: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[int] = mapped_column(Integer, default=0)  # 0=YES_NO, 1=NUMERICAL
    color: Mapped[int] = mapped_column(Integer, default=8)  # palette index 0..19
    position: Mapped[int] = mapped_column(Integer, default=0)
    freq_num: Mapped[int] = mapped_column(Integer, default=1)
    freq_den: Mapped[int] = mapped_column(Integer, default=1)
    reminder_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null = no reminder
    reminder_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_days: Mapped[int] = mapped_column(Integer, default=127)  # 7-bit weekday mask
    target_type: Mapped[int] = mapped_column(Integer, default=0)  # 0=AT_LEAST, 1=AT_MOST
    target_value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EntryRow(Base):
    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="uq_entries_habit_date"),
        Index("ix_entries_habit_date", "habit_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    value: Mapped[int] = mapped_column(Integer)  # UNKNOWN=-1 NO=0 YES_AUTO=1 YES_MANUAL=2 SKIP=3; numeric x1000
    notes: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class RoomRow(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    invite_code: Mapped[str] = mapped_column(Text, unique=True)
    show_leaderboard: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    show_members: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RoomMemberRow(Base):
    __tablename__ = "room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(Text, default="member")  # owner | member
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RoomHabitRow(Base):
    __tablename__ = "room_habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[int] = mapped_column(Integer, default=8)
    freq_num: Mapped[int] = mapped_column(Integer, default=1)
    freq_den: Mapped[int] = mapped_column(Integer, default=1)
    target_type: Mapped[int] = mapped_column(Integer, default=0)
    target_value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class HabitLinkRow(Base):
    __tablename__ = "habit_links"
    __table_args__ = (
        UniqueConstraint("room_habit_id", "user_id", name="uq_habit_links_room_habit_user"),
        UniqueConstraint("habit_id", name="uq_habit_links_habit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_habit_id: Mapped[int] = mapped_column(ForeignKey("room_habits.id", ondelete="CASCADE"), index=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ActivityEventRow(Base):
    __tablename__ = "activity_events"
    __table_args__ = (Index("ix_activity_events_room_id_id", "room_id", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    room_habit_id: Mapped[int | None] = mapped_column(
        ForeignKey("room_habits.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[str] = mapped_column(Text)
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
