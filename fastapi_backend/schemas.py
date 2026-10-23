"""
Request / response models for the HTTP API.

The frontend is written in TypeScript and uses camelCase, so every model
accepts and returns camelCase JSON (``sceneCount``) while Python code uses
snake_case (``scene_count``). This is handled by :class:`ApiModel`.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from core.services.export import ExportFormat
from core.services.images import ImageProviderName
from core.services.video import CompileProviderName, VideoProviderName


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
#: Text providers the user can pick in the UI: a cloud AI or any Ollama model
#: (``ollama:<model>``). ``None`` = automatic fallback.
LLMProviderName = Annotated[str, Field(pattern=r"^(gemini|openai|groq|ollama:\S+)$")]


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
    provider: LLMProviderName | None = None


class ScriptResponse(ApiModel):
    script: str


class SummaryRequest(ApiModel):
    script: str = Field(min_length=1)
    provider: LLMProviderName | None = None


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
    provider: LLMProviderName | None = None


class SplitScenesResponse(ApiModel):
    scenes: list[str]


class ScenePromptRequest(ApiModel):
    text: str
    style: str
    provider: LLMProviderName | None = None


class ScenePromptResponse(ApiModel):
    prompt: str


# ---------------------------------------------------------------------- #
# Media
# ---------------------------------------------------------------------- #
#: Voice-over providers the user can pick in the UI.
VoiceProviderName = Literal["unrealspeech", "kokoro", "piper", "xtts", "melo", "bark"]


class TTSRequest(ApiModel):
    # Emptiness is validated by the core so the error message stays consistent.
    text: str = ""
    voice: str | None = None
    speed: float | None = None
    pitch: float | None = None
    # ``None`` = UnrealSpeech.
    provider: VoiceProviderName | None = None


class VoiceOut(ApiModel):
    id: str
    name: str
    desc: str
    type: str


class VoicesResponse(ApiModel):
    voices: list[VoiceOut]


class ImageRequest(ApiModel):
    prompt: str = Field(min_length=1)
    provider: ImageProviderName | None = None


class UrlResponse(ApiModel):
    url: str


class VideoRequest(ApiModel):
    image_url: str | None = None
    prompt: str | None = None
    # ``None`` = simulated clip.
    provider: VideoProviderName | None = None


class CompileScene(ApiModel):
    # Extra fields sent by the frontend (prompt, selectedImage, ...) are ignored.
    id: int | None = None
    video_url: str | None = None
    # Narration of the scene: its length decides how long the scene stays on screen.
    text: str = ""


class CompileRequest(ApiModel):
    scenes: list[CompileScene] = Field(default_factory=list)
    audio_url: str | None = None
    # ``None`` = simulated render.
    provider: CompileProviderName | None = None


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


# ---------------------------------------------------------------------- #
# AI selection (popup before Step 1)
# ---------------------------------------------------------------------- #
class ProviderStatusResponse(ApiModel):
    id: str
    label: str
    available: bool
    reason: str | None = None
    local: bool = False
    note: str | None = None


class TaskOptionsResponse(ApiModel):
    id: str
    label: str
    coming_soon: bool
    options: list[ProviderStatusResponse]


class AIOptionsResponse(ApiModel):
    tasks: list[TaskOptionsResponse]


class VerifyProviderRequest(ApiModel):
    provider: str = Field(min_length=1)


class HealthResponse(ApiModel):
    status: str
    llm_providers: list[str]
