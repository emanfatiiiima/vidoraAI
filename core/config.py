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
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

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
    leonardo_api_key: str | None = None

    # ------------------------------------------------------------------ #
    # Model selection
    # ------------------------------------------------------------------ #
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"
    openai_text_model: str = "gpt-4o-mini"
    openai_image_model: str = "dall-e-3"
    groq_text_model: str = "llama-3.3-70b-versatile"
    # Leonardo model id (default: Leonardo Phoenix 1.0). Other ids are listed
    # under "Platform models" in the Leonardo API docs.
    leonardo_model_id: str = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"

    # Comma-separated order in which text providers are tried, e.g. "groq,openai".
    # Providers without an API key are skipped automatically.
    llm_provider_order: str = "gemini,openai,groq"

    # ------------------------------------------------------------------ #
    # Local AI (see LOCAL_SETUP.md)
    # ------------------------------------------------------------------ #
    # Hide every cloud provider in the "Choose your AIs" popup.
    local_only: bool = False
    # Ollama server; every pulled model becomes a text option ("ollama:<model>").
    ollama_url: str = "http://127.0.0.1:11434"
    # Context window for Ollama requests (its default is too small for long scripts).
    ollama_num_ctx: int = 8192
    # Ollama model used by automatic (non user-picked) text generation, e.g. "qwen3:8b".
    ollama_default_model: str | None = None
    # GPU worker (``python -m local_ai``) for local voice, image and video models.
    local_ai_url: str = "http://127.0.0.1:8001"
    # One local video clip can take 10+ minutes on an 8 GB card.
    local_ai_timeout_seconds: float = 3600.0
    # Where generated audio, clips and final videos are stored (served at /api/media).
    media_dir: Path = PROJECT_ROOT / "media"
    # FFmpeg binary (name on PATH or full path). ffprobe is looked up next to it.
    ffmpeg_path: str = "ffmpeg"
    # Kdenlive's MLT renderer; auto-detected when empty.
    melt_path: str | None = None
    # Final video size and frame rate (9:16 vertical by default).
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30

    # ------------------------------------------------------------------ #
    # HTTP / server
    # ------------------------------------------------------------------ #
    http_timeout_seconds: float = 60.0
    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Built frontend (``npm run build``) served by FastAPI in production.
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Make the project's ``.env`` file take priority over OS environment variables.

        Editors such as VS Code inject ``.env`` into new terminals as real
        environment variables. Those copies go stale when ``.env`` is edited,
        and would otherwise silently override the fresh values in the file
        (e.g. an old API key -> "Invalid API key"). OS variables still apply
        to any key that is not present in ``.env`` (e.g. in production).
        """
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    # ------------------------------------------------------------------ #
    # Validators / helpers
    # ------------------------------------------------------------------ #
    @field_validator(
        "gemini_api_key",
        "openai_api_key",
        "groq_api_key",
        "serpapi_key",
        "unreal_speech_api_key",
        "leonardo_api_key",
        "ollama_default_model",
        "melt_path",
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
