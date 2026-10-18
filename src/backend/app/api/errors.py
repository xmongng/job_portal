"""Do not expose raw SQL, parameters, tokens or storage paths in API errors."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

logger = logging.getLogger(__name__)


async def database_error_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    code = getattr(exc.orig, "sqlstate", None)
    if code in {"23505", "23503", "40001", "40P01"}:
        return JSONResponse(
            status_code=409, content={"detail": "Resource conflict; check references or retry"}
        )
    if code in {"23514", "23502", "22003", "22007", "22001", "22P02"}:
        return JSONResponse(status_code=422, content={"detail": "Invalid resource data"})
    logger.error("Database request failed: path=%s sqlstate=%s", request.url.path, code)
    return JSONResponse(status_code=500, content={"detail": "Database operation failed"})
