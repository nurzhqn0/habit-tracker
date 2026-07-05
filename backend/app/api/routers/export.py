from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from app.api.deps import CurrentUserDep, SessionDep
from app.application.use_cases import csv_io
from app.domain.errors import ValidationError

router = APIRouter(tags=["export"])

ZIP_MEDIA = "application/zip"
XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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
    return Response(
        data, media_type=XLSX_MEDIA,
        headers={"Content-Disposition": 'attachment; filename="habitflow-export.xlsx"'},
    )


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
    return Response(
        data, media_type=XLSX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="habit-{habit_id}.xlsx"'},
    )


@router.post("/import/csv")
async def import_csv(file: UploadFile, user: CurrentUserDep, session: SessionDep) -> dict:
    data = await file.read(csv_io.MAX_UPLOAD_BYTES + 1)
    if len(data) > csv_io.MAX_UPLOAD_BYTES:
        raise ValidationError("Archive too large")
    return await csv_io.import_zip(session, user.id, data)
