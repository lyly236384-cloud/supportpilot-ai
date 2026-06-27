from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models.schemas import ApiError, ErrorResponse

_logger = logging.getLogger(__name__)


def register_exception_handlers(application) -> None:
    @application.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        payload = ErrorResponse(error=ApiError(code=f"http_{exc.status_code}", message=message))
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = ErrorResponse(
            error=ApiError(code="validation_error", message="Request validation failed"),
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @application.exception_handler(FileNotFoundError)
    async def handle_not_found(_: Request, exc: FileNotFoundError) -> JSONResponse:
        payload = ErrorResponse(error=ApiError(code="not_found", message=str(exc)))
        return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))

    @application.exception_handler(ValueError)
    async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
        """Catch unhandled ValueErrors (e.g. path traversal / invalid input)
        and surface them as 400 Bad Request rather than 500 Internal Server Error."""
        payload = ErrorResponse(error=ApiError(code="bad_request", message=str(exc)))
        return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))

    @application.exception_handler(Exception)
    async def handle_unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
        """Catch-all 500 handler — logs the full trace and returns a safe envelope."""
        _logger.exception("Unhandled server error: %s", exc)
        payload = ErrorResponse(
            error=ApiError(code="internal_error", message="Internal server error"),
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
