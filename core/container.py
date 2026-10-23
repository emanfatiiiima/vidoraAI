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
from core.images import LeonardoClient
from core.llm import LLMProvider, LLMRouter
from core.llm.providers import GeminiProvider, GroqProvider, OpenAIProvider
from core.local import (
    FFmpegCompiler,
    KdenliveCompiler,
    LocalWorkerClient,
    MediaStore,
    MoviePyCompiler,
    OllamaClient,
    RenderSpec,
    provider_resolver,
)
from core.local.ollama import OllamaProvider
from core.services import (
    AIOptionsService,
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
    ai_options: AIOptionsService


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

    # Local text generation: any Ollama model can be picked by name ("ollama:<model>").
    ollama = OllamaClient(http, settings.ollama_url, settings.ollama_num_ctx)
    if settings.ollama_default_model:
        available["ollama"] = OllamaProvider(ollama, settings.ollama_default_model)

    order = settings.provider_order + ([] if "ollama" in settings.provider_order else ["ollama"])
    providers = [available[name] for name in order if name in available]
    if not providers:
        logger.warning("No LLM provider is configured - text generation will fail.")
    else:
        logger.info("LLM providers (in order): %s", ", ".join(p.name for p in providers))

    # Image provider clients - only created when their API key is set.
    leonardo = (
        LeonardoClient(http=http, api_key=settings.leonardo_api_key, model_id=settings.leonardo_model_id)
        if settings.leonardo_api_key
        else None
    )

    llm = LLMRouter(providers, resolver=provider_resolver(ollama))
    research = ResearchService(http, settings.serpapi_key)

    # Local voice / image / video models run on the GPU worker; outputs go to the media folder.
    worker = LocalWorkerClient(http, settings.local_ai_url, settings.local_ai_timeout_seconds)
    media = MediaStore(settings.media_dir, http)
    spec = RenderSpec(settings.video_width, settings.video_height, settings.video_fps)
    ffmpeg = FFmpegCompiler(settings.ffmpeg_path, spec)
    video = VideoService(
        worker=worker,
        media=media,
        compilers=[ffmpeg, MoviePyCompiler(spec), KdenliveCompiler(ffmpeg, settings.melt_path)],
    )

    return Services(
        llm=llm,
        research=research,
        topics=TopicService(llm, research),
        scripts=ScriptService(llm),
        scenes=SceneService(llm),
        tts=TextToSpeechService(http, settings.unreal_speech_api_key, worker=worker, media=media),
        images=ImageService(
            http=http,
            gemini=gemini,
            gemini_model=settings.gemini_image_model,
            openai=openai,
            openai_model=settings.openai_image_model,
            leonardo=leonardo,
            worker=worker,
        ),
        video=video,
        project_export=ProjectExporter(http, media),
        # Provider id -> API key, used to tell the user which AIs they can pick.
        ai_options=AIOptionsService(
            http,
            {
                "gemini": settings.gemini_api_key,
                "openai": settings.openai_api_key,
                "groq": settings.groq_api_key,
                "leonardo": settings.leonardo_api_key,
                "unrealspeech": settings.unreal_speech_api_key,
            },
            ollama=ollama,
            worker=worker,
            compiler_problem=video.compiler_problem,
            local_only=settings.local_only,
        ),
    )
