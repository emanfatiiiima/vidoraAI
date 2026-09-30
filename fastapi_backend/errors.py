"""
Translation of core exceptions into HTTP responses.

Every error leaves the API with the same JSON shape (see
:class:`fastapi_backend.schemas.ErrorResponse`)::

    {"error": "Human readable message", "code": "machine_code", "details": ...}
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions import (
    AllProvidersFailedError,
    CoreError,
    ExternalServiceError,
    InvalidAIResponseError,
    InvalidInputError,
    ProviderFailedError,
    ProviderNotConfiguredError,
)

logger = logging.getLogger(__name__)

# Core exception -> HTTP status code.
_STATUS_BY_EXCEPTION: dict[type[CoreError], int] = {
    InvalidInputError: status.HTTP_400_BAD_REQUEST,
    ProviderNotConfiguredError: status.HTTP_503_SERVICE_UNAVAILABLE,
    AllProvidersFailedError: status.HTTP_503_SERVICE_UNAVAILABLE,
    ProviderFailedError: status.HTTP_502_BAD_GATEWAY,
    InvalidAIResponseError: status.HTTP_502_BAD_GATEWAY,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
}


def _error_body(message: str, code: str, details: Any = None) -> dict[str, Any]:
    return jsonable_encoder({"error": message, "code": code, "details": details})


def _status_for(exc: CoreError) -> int:
    # Rate limits from upstream APIs are forwarded as 429 so the UI can show
    # a "quota reached, wait a moment" message.
    if isinstance(exc, ExternalServiceError) and exc.upstream_status == 429:
        return status.HTTP_429_TOO_MANY_REQUESTS
    for exc_type, code in _STATUS_BY_EXCEPTION.items():
        if isinstance(exc, exc_type):
            return code
    return status.HTTP_500_INTERNAL_SERVER_ERROR


async def _handle_core_error(_: Request, exc: CoreError) -> JSONResponse:
    status_code = _status_for(exc)
    logger.warning("%s (%s): %s", type(exc).__name__, status_code, exc.message)
    return JSONResponse(status_code=status_code, content=_error_body(exc.message, exc.code, exc.details))


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,  # Unprocessable Content
        content=_error_body("Invalid request", "validation_error", exc.errors()),
    )


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body("Internal server error", "internal_error"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to ``app``."""
    app.add_exception_handler(CoreError, _handle_core_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected_error)
