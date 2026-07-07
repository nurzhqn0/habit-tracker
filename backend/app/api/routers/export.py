from datetime import date

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import Response

from app.api.deps import CurrentUserDep, SessionDep
from app.application.use_cases import csv_io, xlsx_reports
from app.domain.errors import ValidationError

router = APIRouter(tags=["export"])

ZIP_MEDIA = "application/zip"
XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_response(data: bytes, filename: str) -> Response:
    return Response(
        data, media_type=XLSX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/csv")
async def export_all_csv(user: CurrentUserDep, session: SessionDep) -> Response:
    data = await csv_io.export_zip(session, user.id)
    return Response(
        data, media_type=ZIP_MEDIA,
        headers={"Content-Disposition": 'attachment; filename="habitflow-export.zip"'},
    )


@router.get("/export/xlsx")
async def export_all_xlsx(user: CurrentUserDep, session: SessionDep) -> Response:
    data = await csv_io.export_xlsx(session, user.id)
    return _xlsx_response(data, "habitflow-export.xlsx")


@router.get("/export/report/xlsx")
async def export_personal_report(
    user: CurrentUserDep,
    session: SessionDep,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> Response:
    data, frm, to = await xlsx_reports.export_personal_xlsx(session, user.id, from_date, to_date)
    return _xlsx_response(data, f"habits-report_{frm}_{to}.xlsx")


@router.get("/rooms/{room_id}/export/xlsx")
async def export_room_report(
    room_id: int,
    user: CurrentUserDep,
    session: SessionDep,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> Response:
    data, frm, to = await xlsx_reports.export_room_xlsx(session, user.id, room_id, from_date, to_date)
    return _xlsx_response(data, f"room-{room_id}-report_{frm}_{to}.xlsx")


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
