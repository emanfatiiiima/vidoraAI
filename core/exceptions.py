"""
Domain exceptions raised by the core.

The core never knows about HTTP. Instead it raises these exceptions and the
backend (``fastapi_backend/errors.py``) translates each one into a proper HTTP
status code and JSON error body. Every exception carries a stable, machine
readable ``code`` that the frontend can switch on.
"""

from __future__ import annotations

from typing import Any


class CoreError(Exception):
    """Base class for every error raised intentionally by the core."""

    code: str = "core_error"

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidInputError(CoreError):
    """The caller supplied invalid input (e.g. empty text for TTS)."""

    code = "invalid_input"


class ProviderNotConfiguredError(CoreError):
    """A required third-party API key is missing from the configuration."""

    code = "provider_not_configured"


class AllProvidersFailedError(CoreError):
    """Every configured AI provider failed (or none is configured)."""

    code = "all_providers_failed"


class InvalidAIResponseError(CoreError):
    """The AI answered, but not in the format we asked for (e.g. bad JSON)."""

    code = "invalid_ai_response"


class ExternalServiceError(CoreError):
    """A third-party HTTP API returned an error.

    ``upstream_status`` keeps the status code of the failed upstream call so
    the backend can forward it to the client when it makes sense.
    """

    code = "external_service_error"

    def __init__(
        self,
        message: str,
        *,
        upstream_status: int | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message, details=details)
        self.upstream_status = upstream_status
