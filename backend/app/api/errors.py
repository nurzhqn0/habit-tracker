from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import ConflictError, DomainError, ForbiddenError, NotFoundError, ValidationError

_STATUS_BY_ERROR = [
    (NotFoundError, 404),
    (ForbiddenError, 403),
    (ConflictError, 409),
    (ValidationError, 422),
]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status = 400
        for error_type, code in _STATUS_BY_ERROR:
            if isinstance(exc, error_type):
                status = code
                break
        return JSONResponse(status_code=status, content={"detail": str(exc)})
