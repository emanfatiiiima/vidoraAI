"""
Dependency wiring ("composition root").

:func:`build_services` is the single place where settings, SDK clients and
services are connected together. Anything that needs the core (the FastAPI
app, a CLI script, a test) calls it once and uses the returned
:class:`Services` bundle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from google import genai
from groq import AsyncGroq
from openai import AsyncOpenAI

from core.config import Settings
from core.llm import LLMProvider, LLMRouter
from core.llm.providers import GeminiProvider, GroqProvider, OpenAIProvider
from core.services import (
    ImageService,
    ProjectExporter,
    ResearchService,
    SceneService,
    ScriptService,
    TextToSpeechService,
    TopicService,
    VideoService,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Services:
    """Every service the application exposes, ready to use."""

    llm: LLMRouter
    research: ResearchService
    topics: TopicService
    scripts: ScriptService
    scenes: SceneService
    tts: TextToSpeechService
    images: ImageService
    video: VideoService
    project_export: ProjectExporter


def build_services(settings: Settings, http: httpx.AsyncClient) -> Services:
    """Create all services from ``settings``.

    Args:
        settings: application configuration.
        http: shared async HTTP client (its lifecycle is owned by the caller).
    """
    gemini = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
    openai = (
        AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.http_timeout_seconds)
        if settings.openai_api_key
        else None
    )
    groq = (
        AsyncGroq(api_key=settings.groq_api_key, timeout=settings.http_timeout_seconds)
        if settings.groq_api_key
        else None
    )

    # Only providers that have an API key are registered, in the configured order.
    available: dict[str, LLMProvider] = {}
    if gemini:
        available["gemini"] = GeminiProvider(gemini, settings.gemini_text_model)
    if openai:
        available["openai"] = OpenAIProvider(openai, settings.openai_text_model)
    if groq:
        available["groq"] = GroqProvider(groq, settings.groq_text_model)

    providers = [available[name] for name in settings.provider_order if name in available]
    if not providers:
        logger.warning("No LLM provider is configured - text generation will fail.")
    else:
        logger.info("LLM providers (in order): %s", ", ".join(p.name for p in providers))

    llm = LLMRouter(providers)
    research = ResearchService(http, settings.serpapi_key)

    return Services(
        llm=llm,
        research=research,
        topics=TopicService(llm, research),
        scripts=ScriptService(llm),
        scenes=SceneService(llm),
        tts=TextToSpeechService(http, settings.unreal_speech_api_key),
        images=ImageService(
            gemini=gemini,
            gemini_model=settings.gemini_image_model,
            openai=openai,
            openai_model=settings.openai_image_model,
        ),
        video=VideoService(),
        project_export=ProjectExporter(http),
    )
