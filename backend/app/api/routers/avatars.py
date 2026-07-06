import time

from aiogram.exceptions import TelegramBadRequest
from fastapi import APIRouter, HTTPException, Request, Response

from app.api.deps import SessionDep
from app.infrastructure.repositories.user_repo import UserRepo

router = APIRouter(tags=["avatars"])

_CACHE_TTL_SECONDS = 3600
_cache: dict[int, tuple[float, bytes | None]] = {}


@router.get("/avatars/{user_id}")
async def get_avatar(user_id: int, request: Request, session: SessionDep) -> Response:
    cached = _cache.get(user_id)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_SECONDS:
        if cached[1] is None:
            raise HTTPException(status_code=404, detail="No avatar")
        return Response(content=cached[1], media_type="image/jpeg", headers=_cache_headers())

    bot = request.app.state.bot
    user = await UserRepo(session).get_by_id(user_id)
    if user is None or bot is None:
        raise HTTPException(status_code=404, detail="No avatar")

    try:
        photos = await bot.get_user_profile_photos(user_id=user.telegram_id, limit=1)
    except TelegramBadRequest:
        photos = None

    if not photos or photos.total_count == 0:
        _cache[user_id] = (time.monotonic(), None)
        raise HTTPException(status_code=404, detail="No avatar")

    file = await bot.get_file(photos.photos[0][-1].file_id)
    buf = await bot.download_file(file.file_path)
    if buf is None:
        raise HTTPException(status_code=404, detail="No avatar")
    data = buf.read()
    _cache[user_id] = (time.monotonic(), data)
    return Response(content=data, media_type="image/jpeg", headers=_cache_headers())


def _cache_headers() -> dict[str, str]:
    return {"Cache-Control": "public, max-age=3600"}
