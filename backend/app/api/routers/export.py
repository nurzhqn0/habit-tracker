import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.deps import CurrentUserDep, SessionDep, SettingsDep
from app.application.use_cases import csv_io, xlsx_reports
from app.domain.errors import ValidationError
from app.infrastructure.db.tables import UserRow
from app.infrastructure.telegram.bot_api import send_document

router = APIRouter(tags=["export"])
logger = logging.getLogger(__name__)

ZIP_MEDIA = "application/zip"
XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Telegram errors that mean the user's chat with the bot is gone for good.
_UNLINKED_MARKERS = ("chat not found", "bot was blocked", "user is deactivated")


def _xlsx_response(data: bytes, filename: str) -> Response:
    return Response(
        data, media_type=XLSX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _deliver(
    user: UserRow, session: SessionDep, settings: SettingsDep,
    data: bytes, filename: str, caption: str, media: str,
) -> Response:
    """Sends the file to the user's Telegram chat instead of returning it for download."""
    if not user.bot_linked:
        raise ValidationError("Connect the Telegram bot first, then export again.")
    error = await send_document(settings.bot_token, user.telegram_id, filename, data, caption)
    if error is None:
        return JSONResponse({"ok": True, "delivered": "telegram"})
    logger.warning("telegram delivery failed for user %s: %s", user.id, error)
    if any(marker in error.lower() for marker in _UNLINKED_MARKERS):
        # The chat is gone (bot blocked / never started) — unlink so Settings
        # shows the real state and the user is told to reconnect.
        user.bot_linked = False
        await session.commit()
        raise ValidationError("Connect the Telegram bot first, then export again.")
    raise HTTPException(status_code=502, detail="Telegram could not deliver the file.")


@router.get("/export/csv")
async def export_all_csv(
    user: CurrentUserDep, session: SessionDep, settings: SettingsDep, to_telegram: bool = False
) -> Response:
    data = await csv_io.export_zip(session, user.id)
    if to_telegram:
        return await _deliver(user, session, settings, data, "habitflow-export.zip", "Your HabitFlow export", ZIP_MEDIA)
    return Response(
        data, media_type=ZIP_MEDIA,
        headers={"Content-Disposition": 'attachment; filename="habitflow-export.zip"'},
    )


@router.get("/export/xlsx")
async def export_all_xlsx(
    user: CurrentUserDep, session: SessionDep, settings: SettingsDep, to_telegram: bool = False
) -> Response:
    data = await csv_io.export_xlsx(session, user.id)
    if to_telegram:
        return await _deliver(user, session, settings, data, "habitflow-export.xlsx", "Your HabitFlow export", XLSX_MEDIA)
    return _xlsx_response(data, "habitflow-export.xlsx")


@router.get("/export/report/xlsx")
async def export_personal_report(
    user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    to_telegram: bool = False,
) -> Response:
    data, frm, to = await xlsx_reports.export_personal_xlsx(session, user.id, from_date, to_date)
    filename = f"habits-report_{frm}_{to}.xlsx"
    if to_telegram:
        return await _deliver(user, session, settings, data, filename, f"Habits report {frm} → {to}", XLSX_MEDIA)
    return _xlsx_response(data, filename)


@router.get("/rooms/{room_id}/export/xlsx")
async def export_room_report(
    room_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    to_telegram: bool = False,
) -> Response:
    data, frm, to = await xlsx_reports.export_room_xlsx(session, user.id, room_id, from_date, to_date)
    filename = f"room-{room_id}-report_{frm}_{to}.xlsx"
    if to_telegram:
        return await _deliver(user, session, settings, data, filename, f"Room report {frm} → {to}", XLSX_MEDIA)
    return _xlsx_response(data, filename)


@router.get("/habits/{habit_id}/export/csv")
async def export_habit_csv(habit_id: int, user: CurrentUserDep, session: SessionDep) -> Response:
    data = await csv_io.export_zip(session, user.id, habit_id)
    return Response(
        data, media_type=ZIP_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="habit-{habit_id}.zip"'},
    )


@router.get("/habits/{habit_id}/export/xlsx")
async def export_habit_xlsx(habit_id: int, user: CurrentUserDep, session: SessionDep) -> Response:
    data = await csv_io.export_xlsx(session, user.id, habit_id)
    return _xlsx_response(data, f"habit-{habit_id}.xlsx")


@router.post("/import/csv")
async def import_csv(file: UploadFile, user: CurrentUserDep, session: SessionDep) -> dict:
    data = await file.read(csv_io.MAX_UPLOAD_BYTES + 1)
    if len(data) > csv_io.MAX_UPLOAD_BYTES:
        raise ValidationError("Archive too large")
    return await csv_io.import_zip(session, user.id, data)
