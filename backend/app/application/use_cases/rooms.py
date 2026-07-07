from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application import habit_math
from app.application.use_cases import habits as habits_uc
from app.domain.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.domain.models.entry import SKIP, YES_MANUAL
from app.infrastructure.db.tables import HabitLinkRow, HabitRow, RoomHabitRow, RoomRow
from app.infrastructure.repositories.habit_repo import EntryRepo, HabitRepo
from app.infrastructure.repositories.room_repo import RoomRepo, generate_invite_code
from app.infrastructure.repositories.user_repo import UserRepo

ROOM_HABIT_FIELDS = {
    "name", "description", "type", "color", "freq_num", "freq_den",
    "target_type", "target_value", "unit",
}


async def _require_member(session: AsyncSession, room_id: int, user_id: int) -> RoomRow:
    repo = RoomRepo(session)
    room = await repo.get(room_id)
    if await repo.membership(room_id, user_id) is None:
        raise NotFoundError("Room not found")
    return room


async def _require_owner(session: AsyncSession, room_id: int, user_id: int) -> RoomRow:
    room = await _require_member(session, room_id, user_id)
    if room.owner_id != user_id:
        raise ForbiddenError("Only the room owner can do this")
    return room


async def _require_admin(session: AsyncSession, room_id: int, user_id: int) -> RoomRow:
    room = await _require_member(session, room_id, user_id)
    if room.owner_id == user_id:
        return room
    membership = await RoomRepo(session).membership(room_id, user_id)
    if membership.role not in ("owner", "admin"):
        raise ForbiddenError("Only room admins can do this")
    return room


async def create_room(session: AsyncSession, user_id: int, name: str, description: str) -> RoomRow:
    if not name.strip():
        raise ValidationError("Room name must not be empty")
    room = await RoomRepo(session).create(user_id, name.strip(), description)
    await session.commit()
    return room


async def update_room(session: AsyncSession, user_id: int, room_id: int, fields: dict) -> RoomRow:
    room = await _require_owner(session, room_id, user_id)
    if "name" in fields and fields["name"] is not None:
        if not str(fields["name"]).strip():
            raise ValidationError("Room name must not be empty")
        room.name = str(fields["name"]).strip()
    if "description" in fields and fields["description"] is not None:
        room.description = fields["description"]
    await session.commit()
    return room


async def delete_room(session: AsyncSession, user_id: int, room_id: int) -> None:
    room = await _require_owner(session, room_id, user_id)
    await session.delete(room)
    await session.commit()


async def rotate_invite(session: AsyncSession, user_id: int, room_id: int) -> str:
    room = await _require_admin(session, room_id, user_id)
    room.invite_code = generate_invite_code()
    await session.commit()
    return room.invite_code


async def invite_by_username(
    session: AsyncSession, bot, user_id: int, room_id: int, username: str, join_link: str
) -> tuple[str, str]:
    """Invites a user by Telegram username; returns (status, normalized username)."""
    room = await _require_admin(session, room_id, user_id)
    uname = username.strip().lstrip("@")
    target = await UserRepo(session).find_by_username(uname)
    if target is None:
        return "not_registered", uname
    if await RoomRepo(session).membership(room_id, target.id) is not None:
        return "already_member", uname
    if bot is None:
        return "not_linked", uname

    from aiogram.exceptions import TelegramAPIError
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    inviter = await UserRepo(session).get_by_id(user_id)
    try:
        await bot.send_message(
            target.telegram_id,
            f"👋 {inviter.first_name} invited you to join *{room.name}* on HabitFlow",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Join room", url=join_link)]]
            ),
        )
    except TelegramAPIError:
        return "not_linked", uname
    if not target.bot_linked:
        # Delivery succeeded, so the user has started the bot; heal a stale flag.
        target.bot_linked = True
        await session.commit()
    return "sent", uname


async def join_room(session: AsyncSession, user_id: int, code: str) -> RoomRow:
    repo = RoomRepo(session)
    room = await repo.get_by_invite_code(code)
    if room is None:
        raise NotFoundError("Invalid invite code")
    if await repo.membership(room.id, user_id) is not None:
        return room
    from app.infrastructure.db.tables import RoomMemberRow

    session.add(RoomMemberRow(room_id=room.id, user_id=user_id, role="member"))
    await repo.add_event(room.id, user_id, "member_joined")
    await session.commit()
    return room


async def remove_member(session: AsyncSession, user_id: int, room_id: int, target_user_id: int) -> None:
    repo = RoomRepo(session)
    room = await _require_member(session, room_id, user_id)
    if target_user_id != user_id and room.owner_id != user_id:
        actor = await repo.membership(room_id, user_id)
        target = await repo.membership(room_id, target_user_id)
        if actor.role != "admin" or (target is not None and target.role != "member"):
            raise ForbiddenError("Only the room owner or an admin can remove members")
    if target_user_id == room.owner_id:
        raise ValidationError("The owner cannot leave their own room; delete it instead")

    membership = await repo.membership(room_id, target_user_id)
    if membership is None:
        raise NotFoundError("Member not found")

    # Unlink the member's habits from this room.
    for room_habit in await repo.room_habits(room_id, include_archived=True):
        link = await repo.link_for_user(room_habit.id, target_user_id)
        if link is not None:
            await session.delete(link)

    await session.delete(membership)
    await repo.add_event(room_id, target_user_id, "member_left")
    await session.commit()


async def set_member_role(
    session: AsyncSession, user_id: int, room_id: int, target_user_id: int, role: str
) -> None:
    room = await _require_owner(session, room_id, user_id)
    if target_user_id == room.owner_id:
        raise ValidationError("The owner's role cannot be changed; transfer ownership instead")
    membership = await RoomRepo(session).membership(room_id, target_user_id)
    if membership is None:
        raise NotFoundError("Member not found")
    membership.role = role
    await session.commit()


async def transfer_ownership(
    session: AsyncSession, user_id: int, room_id: int, target_user_id: int
) -> RoomRow:
    room = await _require_owner(session, room_id, user_id)
    if target_user_id == user_id:
        raise ValidationError("You already own this room")
    repo = RoomRepo(session)
    target = await repo.membership(room_id, target_user_id)
    if target is None:
        raise NotFoundError("Member not found")
    old_owner = await repo.membership(room_id, user_id)
    room.owner_id = target_user_id
    target.role = "owner"
    old_owner.role = "admin"
    await session.commit()
    return room


async def create_room_habit(session: AsyncSession, user_id: int, room_id: int, fields: dict) -> RoomHabitRow:
    await _require_admin(session, room_id, user_id)
    if not str(fields.get("name", "")).strip():
        raise ValidationError("Habit name must not be empty")
    habit = RoomHabitRow(
        room_id=room_id, created_by=user_id,
        **{k: v for k, v in fields.items() if k in ROOM_HABIT_FIELDS},
    )
    session.add(habit)
    await session.flush()
    await RoomRepo(session).add_event(room_id, user_id, "room_habit_created", room_habit_id=habit.id)
    await session.commit()
    return habit


async def update_room_habit(
    session: AsyncSession, user_id: int, room_id: int, room_habit_id: int, fields: dict
) -> RoomHabitRow:
    await _require_admin(session, room_id, user_id)
    habit = await RoomRepo(session).get_room_habit(room_id, room_habit_id)
    for key, value in fields.items():
        if key in ROOM_HABIT_FIELDS or key == "archived":
            setattr(habit, key, value)
    await session.commit()
    return habit


async def delete_room_habit(session: AsyncSession, user_id: int, room_id: int, room_habit_id: int) -> None:
    await _require_admin(session, room_id, user_id)
    habit = await RoomRepo(session).get_room_habit(room_id, room_habit_id)
    await session.delete(habit)
    await session.commit()


async def link_habit(
    session: AsyncSession, user_id: int, room_id: int, room_habit_id: int, habit_id: int | None
) -> HabitRow:
    """Links an existing personal habit, or creates one from the room habit template."""
    await _require_member(session, room_id, user_id)
    repo = RoomRepo(session)
    room_habit = await repo.get_room_habit(room_id, room_habit_id)

    if await repo.link_for_user(room_habit_id, user_id) is not None:
        raise ConflictError("You already linked a habit to this room habit")

    if habit_id is not None:
        habit = await HabitRepo(session).get_owned(habit_id, user_id)
        if habit.type != room_habit.type:
            raise ValidationError("Habit type does not match the room habit")
        existing_link = await repo.link_for_habit(habit.id)
        if existing_link is not None:
            raise ConflictError("This habit is already linked to a room habit")
    else:
        habit = await HabitRepo(session).create(
            user_id,
            name=room_habit.name,
            description=room_habit.description,
            type=room_habit.type,
            color=room_habit.color,
            freq_num=room_habit.freq_num,
            freq_den=room_habit.freq_den,
            target_type=room_habit.target_type,
            target_value=room_habit.target_value,
            unit=room_habit.unit,
        )

    session.add(HabitLinkRow(room_habit_id=room_habit_id, habit_id=habit.id, user_id=user_id))
    await repo.add_event(room_id, user_id, "habit_linked", room_habit_id=room_habit_id)
    await session.commit()
    return habit


async def unlink_habit(session: AsyncSession, user_id: int, room_id: int, room_habit_id: int) -> None:
    await _require_member(session, room_id, user_id)
    repo = RoomRepo(session)
    link = await repo.link_for_user(room_habit_id, user_id)
    if link is None:
        raise NotFoundError("No linked habit")
    await session.delete(link)
    await session.commit()


@dataclass
class LeaderboardRow:
    user_id: int
    first_name: str
    username: str | None
    photo_url: str | None
    score: float
    streak: int
    completions: int
    linked_habits: int


def _is_success(habit_row: HabitRow, value: int) -> bool:
    if habit_row.type == 1:
        if habit_row.target_type == 0:
            return value / 1000.0 >= habit_row.target_value
        return value != -1 and value / 1000.0 <= habit_row.target_value
    return value in (YES_MANUAL, SKIP) or value == 1


async def leaderboard(
    session: AsyncSession, user_id: int, room_id: int, period: str = "week"
) -> list[LeaderboardRow]:
    await _require_member(session, room_id, user_id)
    repo = RoomRepo(session)
    members = await repo.members_with_users(room_id)
    room_habits = await repo.room_habits(room_id)
    links = await repo.links_for_room_habits([rh.id for rh in room_habits])
    links_by_user: dict[int, list[HabitLinkRow]] = {}
    for link in links:
        links_by_user.setdefault(link.user_id, []).append(link)

    habit_repo = HabitRepo(session)
    entry_repo = EntryRepo(session)
    user_repo = UserRepo(session)

    rows: list[LeaderboardRow] = []
    for membership, user in members:
        prefs = await user_repo.get_or_create_preferences(user.id)
        today = habit_math.user_today(prefs)
        if period == "week":
            since = today - timedelta(days=6)
        elif period == "month":
            since = today - timedelta(days=29)
        else:
            since = Date(1970, 1, 1)

        best_score = 0.0
        best_streak = 0
        completions = 0
        user_links = links_by_user.get(user.id, [])

        for link in user_links:
            try:
                habit_row = await habit_repo.get_owned(link.habit_id, user.id)
            except NotFoundError:
                continue
            habit = habit_math.to_domain(habit_row)
            entry_rows = await entry_repo.all_for_habit(habit_row.id)
            computed = habit_math.computed_entries_for(habit, entry_rows)
            best_score = max(best_score, habit_math.score_on(habit, computed, today))
            best_streak = max(best_streak, habit_math.current_streak(habit, computed, today))
            completions += sum(
                1
                for d, e in computed.items()
                if since <= d <= today and _is_success(habit_row, e.value)
            )

        rows.append(
            LeaderboardRow(
                user_id=user.id,
                first_name=user.first_name,
                username=user.username,
                photo_url=f"/api/v1/avatars/{user.id}",
                score=best_score,
                streak=best_streak,
                completions=completions,
                linked_habits=len(user_links),
            )
        )

    rows.sort(key=lambda r: (-r.score, -r.completions, -r.streak))
    return rows


async def authorize_member_habit(
    session: AsyncSession, caller_id: int, room_id: int, member_id: int, habit_id: int
) -> None:
    """Read access for room admins/owners to a member's habit, only if linked into this room."""
    await _require_admin(session, room_id, caller_id)
    repo = RoomRepo(session)
    if await repo.membership(room_id, member_id) is None:
        raise NotFoundError("Member not found")
    link = await repo.link_for_habit(habit_id)
    if link is None or link.user_id != member_id:
        raise NotFoundError("Habit not found")
    room_habit = await session.get(RoomHabitRow, link.room_habit_id)
    if room_habit is None or room_habit.room_id != room_id:
        raise NotFoundError("Habit not found")


async def member_overview(
    session: AsyncSession,
    caller_id: int,
    room_id: int,
    member_id: int,
    from_date: Date,
    to_date: Date,
) -> list[habits_uc.HabitOverviewItem]:
    await _require_admin(session, room_id, caller_id)
    repo = RoomRepo(session)
    if await repo.membership(room_id, member_id) is None:
        raise NotFoundError("Member not found")
    room_habits = await repo.room_habits(room_id)
    links = await repo.links_for_room_habits([rh.id for rh in room_habits])
    habit_ids = [link.habit_id for link in links if link.user_id == member_id]
    return await habits_uc.get_overview(
        session, member_id, from_date, to_date, include_archived=True, habit_ids=habit_ids
    )


async def record_entry_activity(
    session: AsyncSession, user_id: int, habit_row: HabitRow, entry_date: Date, value: int
) -> None:
    """Called after an entry change on a linked habit: logs a completion event."""
    repo = RoomRepo(session)
    link = await repo.link_for_habit(habit_row.id)
    if link is None or link.user_id != user_id:
        return
    if not _is_success(habit_row, value) or value == SKIP:
        return
    room_habit = await session.get(RoomHabitRow, link.room_habit_id)
    if room_habit is None:
        return
    await repo.add_event(
        room_habit.room_id, user_id, "entry_completed",
        room_habit_id=room_habit.id, entry_date=entry_date, value=value,
    )
