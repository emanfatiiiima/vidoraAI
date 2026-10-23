"""
AI selection (shown before Step 1 of the video pipeline).

Before a project starts, the user picks one AI per task (topics, script,
voice-over, images, video, final render). This service answers two questions
for that popup:

* :meth:`AIOptionsService.list_tasks` - which AIs exist for each task and
  whether they can be used: cloud AIs need their API key, local AIs need
  Ollama / the GPU worker running and the model downloaded.
* :meth:`AIOptionsService.verify` - does it actually work? For cloud AIs it
  calls a free endpoint of the provider (e.g. "list models"), so an invalid
  or expired key is reported *before* the user starts, not halfway through.

Cloud providers are listed below; local model ids and labels come from
:mod:`local_ai.catalog`. The frontend only renders what this service returns.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx

from core.exceptions import ProviderNotConfiguredError
from core.local import LocalWorkerClient, OllamaClient, OllamaError
from core.local.ollama import PREFIX as OLLAMA_PREFIX
from local_ai.catalog import COMPILERS, ENGINES, engine_ids

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- #
# Catalog
# ---------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """Static facts about one cloud AI provider."""

    label: str
    #: Name of the ``.env`` variable that holds its key (shown in error messages).
    env_var: str
    #: Free, authenticated endpoint used to check the key. ``None`` = presence check only.
    check_url: str | None = None
    #: Header the key is sent in, and its prefix.
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "


PROVIDERS: dict[str, ProviderInfo] = {
    "gemini": ProviderInfo(
        label="Gemini",
        env_var="GEMINI_API_KEY",
        check_url="https://generativelanguage.googleapis.com/v1beta/models",
        auth_header="x-goog-api-key",
        auth_prefix="",
    ),
    "openai": ProviderInfo(
        label="ChatGPT",
        env_var="OPENAI_API_KEY",
        check_url="https://api.openai.com/v1/models",
    ),
    "groq": ProviderInfo(
        label="Groq",
        env_var="GROQ_API_KEY",
        check_url="https://api.groq.com/openai/v1/models",
    ),
    "leonardo": ProviderInfo(
        label="Leonardo",
        env_var="LEONARDO_API_KEY",
        check_url="https://cloud.leonardo.ai/api/rest/v1/me",
    ),
    # UnrealSpeech has no free "who am I" endpoint, so only the key's presence is checked.
    "unrealspeech": ProviderInfo(label="UnrealSpeech", env_var="UNREAL_SPEECH_API_KEY"),
}

#: Placeholder in a task's provider list, expanded to every installed Ollama model.
OLLAMA_MODELS = "ollama:*"


@dataclass(frozen=True, slots=True)
class TaskInfo:
    """One task the user picks an AI for."""

    id: str
    label: str
    #: Local options first, then cloud ones.
    providers: tuple[str, ...]
    #: True while the task has no real implementation yet (shown as "coming soon").
    coming_soon: bool = False


TASKS: tuple[TaskInfo, ...] = (
    TaskInfo("topics", "Topic ideas", (OLLAMA_MODELS, "gemini", "openai", "groq")),
    TaskInfo("script", "Script writing", (OLLAMA_MODELS, "gemini", "openai", "groq")),
    TaskInfo("voice", "Voice-over", (*engine_ids("tts"), "unrealspeech")),
    TaskInfo("image", "Image generation", (*engine_ids("image"), "openai", "leonardo", "gemini")),
    TaskInfo("video", "Video generation", engine_ids("video")),
    TaskInfo("compile", "Final render", tuple(COMPILERS)),
)


# ---------------------------------------------------------------------- #
# Results
# ---------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ProviderStatus:
    """Whether a provider can be used, and why not if it can't."""

    id: str
    label: str
    available: bool
    reason: str | None = None
    #: Runs on this machine (no API key, no internet).
    local: bool = False
    #: Short tip shown under the option (speed, quality, caveats).
    note: str | None = None


@dataclass(frozen=True, slots=True)
class TaskOptions:
    """A task together with the status of each of its providers."""

    id: str
    label: str
    coming_soon: bool
    options: list[ProviderStatus] = field(default_factory=list)


# ---------------------------------------------------------------------- #
# Service
# ---------------------------------------------------------------------- #
class AIOptionsService:
    """Reports which AI providers can be used and whether they work."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        api_keys: dict[str, str | None],
        *,
        ollama: OllamaClient | None = None,
        worker: LocalWorkerClient | None = None,
        compiler_problem: Callable[[str], str | None] | None = None,
        local_only: bool = False,
    ) -> None:
        """
        Args:
            http: shared async HTTP client.
            api_keys: cloud provider id -> API key (``None`` when not configured).
            ollama: Ollama client (local text models).
            worker: GPU worker client (local voice/image/video models).
            compiler_problem: why a renderer (ffmpeg, moviepy, kdenlive) can't run, or ``None``.
            local_only: hide every cloud provider.
        """
        self._http = http
        self._api_keys = api_keys
        self._ollama = ollama
        self._worker = worker
        self._compiler_problem = compiler_problem
        self._local_only = local_only

    async def list_tasks(self) -> list[TaskOptions]:
        """Every task with its providers and whether they can be used right now."""
        ollama_models, ollama_problem = await self._ollama_models()
        worker_engines, worker_problem = await self._worker_engines()

        tasks = []
        for task in TASKS:
            options: list[ProviderStatus] = []
            for provider in task.providers:
                if provider == OLLAMA_MODELS:
                    options += self._ollama_options(ollama_models, ollama_problem)
                elif provider in PROVIDERS:
                    if not self._local_only:
                        options.append(self._key_status(provider))
                else:
                    options.append(self._local_status(provider, worker_engines, worker_problem))
            tasks.append(TaskOptions(id=task.id, label=task.label, coming_soon=task.coming_soon, options=options))
        return tasks

    async def verify(self, provider: str) -> ProviderStatus:
        """Check that ``provider`` is usable right now.

        Never raises - problems are reported through ``reason``.
        """
        if provider.startswith(OLLAMA_PREFIX):
            models, problem = await self._ollama_models()
            model = provider[len(OLLAMA_PREFIX):]
            if problem is None and model not in models:
                problem = f"Ollama has no model '{model}'. Run: ollama pull {model}"
            return self._ollama_status(model, problem)
        if provider in ENGINES or provider in COMPILERS:
            engines, problem = await self._worker_engines() if provider in ENGINES else ({}, None)
            return self._local_status(provider, engines, problem)

        status = self._key_status(provider)
        info = PROVIDERS.get(provider)
        if not status.available or info is None or info.check_url is None:
            return status

        key = self._api_keys[provider]
        try:
            response = await self._http.get(
                info.check_url,
                headers={info.auth_header: f"{info.auth_prefix}{key}"},
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            logger.warning("%s key check could not reach the provider: %s", info.label, exc)
            return self._unavailable(provider, f"Could not reach {info.label}. Please try again.")

        if response.status_code in (400, 401, 403):
            # Gemini answers 400 (API_KEY_INVALID); the others 401/403.
            return self._unavailable(
                provider, f"{info.label}'s API key ({info.env_var}) is invalid or expired."
            )
        if response.status_code == 429:
            return self._unavailable(provider, f"{info.label} has reached its quota limit.")
        if response.is_error:
            return self._unavailable(
                provider, f"{info.label} returned an error ({response.status_code})."
            )
        return status

    # ------------------------------------------------------------------ #
    # Local providers
    # ------------------------------------------------------------------ #
    async def _ollama_models(self) -> tuple[list[str], str | None]:
        if self._ollama is None:
            return [], "Ollama is not configured (OLLAMA_URL)."
        try:
            models = await self._ollama.list_models()
        except OllamaError as exc:
            return [], str(exc)
        if not models:
            return [], "Ollama has no models yet. Run e.g.: ollama pull qwen3:8b"
        return models, None

    def _ollama_options(self, models: list[str], problem: str | None) -> list[ProviderStatus]:
        if problem:
            return [self._ollama_status(None, problem)]
        return [self._ollama_status(model, None) for model in models]

    @staticmethod
    def _ollama_status(model: str | None, problem: str | None) -> ProviderStatus:
        return ProviderStatus(
            id=f"{OLLAMA_PREFIX}{model}" if model else "ollama",
            label=f"Ollama · {model}" if model else "Ollama",
            available=problem is None,
            reason=problem,
            local=True,
        )

    async def _worker_engines(self) -> tuple[dict, str | None]:
        if self._worker is None:
            return {}, "The local AI worker is not configured (LOCAL_AI_URL)."
        try:
            health = await self._worker.health()
        except ProviderNotConfiguredError as exc:
            hint = (exc.details or {}).get("hint", "")
            return {}, f"{exc.message} {hint}".strip()
        return health.get("engines") or {}, None

    def _local_status(self, provider: str, engines: dict, worker_problem: str | None) -> ProviderStatus:
        if provider in COMPILERS:
            problem = (
                self._compiler_problem(provider) if self._compiler_problem else "Renderers are not configured."
            )
            return ProviderStatus(provider, COMPILERS[provider], problem is None, problem, local=True)

        engine = ENGINES.get(provider)
        if engine is None:
            return ProviderStatus(id=provider, label=provider, available=False, reason="Unknown AI provider.")
        status = engines.get(provider) or {}
        problem = worker_problem or (None if status.get("available") else status.get("reason") or "Not available.")
        return ProviderStatus(provider, engine.label, problem is None, problem, local=True, note=engine.note)

    # ------------------------------------------------------------------ #
    # Cloud providers
    # ------------------------------------------------------------------ #
    def _key_status(self, provider: str) -> ProviderStatus:
        """Available when the provider is known and its API key is set."""
        info = PROVIDERS.get(provider)
        if info is None:
            return ProviderStatus(id=provider, label=provider, available=False, reason="Unknown AI provider.")
        if not self._api_keys.get(provider):
            return self._unavailable(provider, f"{info.label}'s API key ({info.env_var}) is not set on the server.")
        return ProviderStatus(id=provider, label=info.label, available=True)

    @staticmethod
    def _unavailable(provider: str, reason: str) -> ProviderStatus:
        return ProviderStatus(id=provider, label=PROVIDERS[provider].label, available=False, reason=reason)
