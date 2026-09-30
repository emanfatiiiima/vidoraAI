"""
Request / response models for the HTTP API.

The frontend is written in TypeScript and uses camelCase, so every model
accepts and returns camelCase JSON (``sceneCount``) while Python code uses
snake_case (``scene_count``). This is handled by :class:`ApiModel`.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from core.services.export import ExportFormat


class ApiModel(BaseModel):
    """Base model: camelCase over the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------- #
# Errors
# ---------------------------------------------------------------------- #
class ErrorResponse(ApiModel):
    """Shape of every error returned by the API."""

    error: str
    code: str
    details: Any | None = None


# ---------------------------------------------------------------------- #
# Generic text generation
# ---------------------------------------------------------------------- #
class GenerateRequest(ApiModel):
    prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    # Kept for compatibility with the original API: "application/json" enables JSON mode.
    response_mime_type: str | None = None


class GenerateResponse(ApiModel):
    text: str
    provider: str


# ---------------------------------------------------------------------- #
# Topics & research
# ---------------------------------------------------------------------- #
#: Text providers the user can pick in the UI. ``None`` = automatic fallback.
LLMProviderName = Literal["gemini", "openai", "groq"]


class BasicTopicsRequest(ApiModel):
    niche: str = Field(min_length=1)
    duration: str
    audience: str | None = None
    provider: LLMProviderName | None = None


class NicheRequest(ApiModel):
    niche: str = Field(min_length=1)
    provider: LLMProviderName | None = None


class TopicsResponse(ApiModel):
    topics: list[str]


class NewsResponse(ApiModel):
    headlines: list[str]


# ---------------------------------------------------------------------- #
# Script
# ---------------------------------------------------------------------- #
class ScriptRequest(ApiModel):
    topic: str = Field(min_length=1)
    niche: str
    duration: str
    style: str


class ScriptResponse(ApiModel):
    script: str


class SummaryRequest(ApiModel):
    script: str = Field(min_length=1)


class SummaryResponse(ApiModel):
    summary: str


class ExportRequest(ApiModel):
    topic: str
    script: str
    format: ExportFormat = ExportFormat.TXT


# ---------------------------------------------------------------------- #
# Scenes
# ---------------------------------------------------------------------- #
class SplitScenesRequest(ApiModel):
    script: str = Field(min_length=1)
    scene_count: int = Field(ge=1, le=50)


class SplitScenesResponse(ApiModel):
    scenes: list[str]


class ScenePromptRequest(ApiModel):
    text: str
    style: str


class ScenePromptResponse(ApiModel):
    prompt: str


# ---------------------------------------------------------------------- #
# Media
# ---------------------------------------------------------------------- #
class TTSRequest(ApiModel):
    # Emptiness is validated by the core so the error message stays consistent.
    text: str = ""
    voice: str | None = None
    speed: float | None = None
    pitch: float | None = None


class ImageRequest(ApiModel):
    prompt: str = Field(min_length=1)


class UrlResponse(ApiModel):
    url: str


class VideoRequest(ApiModel):
    image_url: str | None = None
    prompt: str | None = None


class CompileScene(ApiModel):
    # Extra fields sent by the frontend (text, prompt, ...) are ignored.
    id: int | None = None
    video_url: str | None = None


class CompileRequest(ApiModel):
    scenes: list[CompileScene] = Field(default_factory=list)
    audio_url: str | None = None


class VideoResponse(ApiModel):
    url: str
    status: str


# ---------------------------------------------------------------------- #
# Project export (Step 8)
# ---------------------------------------------------------------------- #
class ProjectSceneIn(ApiModel):
    # Matches the scene objects kept by the frontend; extra fields are ignored.
    text: str = ""
    prompt: str = ""
    selected_image: str | None = None
    video_url: str | None = None


class ProjectExportRequest(ApiModel):
    niche: str = ""
    style: str = ""
    duration: str = ""
    aspect_ratio: str = ""
    scene_count: int | None = None
    topic: str = ""
    script: str = ""
    summary: str = ""
    audio_url: str | None = None
    final_video_url: str | None = None
    scenes: list[ProjectSceneIn] = Field(default_factory=list)


class HealthResponse(ApiModel):
    status: str
    llm_providers: list[str]
