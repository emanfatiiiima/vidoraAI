"""
Application settings.

All configuration is read from environment variables (or the ``.env`` file in
the project root) and validated by Pydantic. Nothing else in the codebase
should read ``os.environ`` directly - always go through :class:`Settings`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = the folder that contains ``core/``, ``fastapi_backend/`` and ``frontend/``.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Strongly-typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # the .env file may contain keys used by other tools
    )

    # ------------------------------------------------------------------ #
    # API keys (all optional - features degrade gracefully when missing)
    # ------------------------------------------------------------------ #
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    serpapi_key: str | None = None
    unreal_speech_api_key: str | None = None

    # ------------------------------------------------------------------ #
    # Model selection
    # ------------------------------------------------------------------ #
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"
    groq_text_model: str = "llama-3.3-70b-versatile"

    # Comma-separated order in which text providers are tried, e.g. "groq,openai".
    # Providers without an API key are skipped automatically.
    llm_provider_order: str = "gemini,openai,groq"

    # ------------------------------------------------------------------ #
    # HTTP / server
    # ------------------------------------------------------------------ #
    http_timeout_seconds: float = 60.0
    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Built frontend (``npm run build``) served by FastAPI in production.
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"

    # ------------------------------------------------------------------ #
    # Validators / helpers
    # ------------------------------------------------------------------ #
    @field_validator(
        "gemini_api_key",
        "openai_api_key",
        "groq_api_key",
        "serpapi_key",
        "unreal_speech_api_key",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        """Treat ``KEY=`` (empty value in .env) the same as a missing key."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def provider_order(self) -> list[str]:
        """``llm_provider_order`` parsed into a clean, lower-case list."""
        return [p.strip().lower() for p in self.llm_provider_order.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        """``cors_origins`` parsed into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (read once per process)."""
    return Settings()
