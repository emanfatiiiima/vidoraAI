"""
Ollama - local text generation (topics, scripts, scene prompts).

Every model pulled into Ollama (``ollama pull qwen3:8b``) is offered in the
"Choose your AIs" popup as ``ollama:<model>``. Providers are created on demand,
so models pulled while the server runs show up without a restart.
"""

from __future__ import annotations

import re

import httpx

from core.llm.base import LLMProvider, LLMRequest
from core.llm.providers import EmptyResponseError

PREFIX = "ollama:"
# Reasoning models (qwen3, deepseek-r1) may put their thinking in the answer.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
# Loading a model from disk + writing a long script on a mid-range GPU.
GENERATE_TIMEOUT_SECONDS = 900.0


class OllamaError(RuntimeError):
    """Ollama is unreachable or rejected the request (message is user-facing)."""


class OllamaClient:
    """Minimal async client for the Ollama REST API."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, num_ctx: int = 8192) -> None:
        self._http = http
        self.base_url = base_url.rstrip("/")
        self._num_ctx = num_ctx

    async def list_models(self) -> list[str]:
        """Names of the installed models (e.g. ``["qwen3:8b", "mistral:latest"]``).

        Raises:
            OllamaError: Ollama is not running.
        """
        try:
            response = await self._http.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama is not running at {self.base_url}. Start the Ollama app.") from exc
        return sorted(m["name"] for m in response.json().get("models") or [] if m.get("name"))

    async def chat(self, model: str, request: LLMRequest) -> str:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": self._num_ctx},
        }
        if request.json_mode:
            payload["format"] = "json"

        try:
            response = await self._http.post(
                f"{self.base_url}/api/chat", json=payload, timeout=GENERATE_TIMEOUT_SECONDS
            )
        except httpx.HTTPError as exc:
            raise OllamaError(f"Could not reach Ollama at {self.base_url}: {exc}") from exc
        if response.is_error:
            try:
                reason = response.json().get("error") or response.text
            except ValueError:
                reason = response.text
            raise OllamaError(f"Ollama error ({response.status_code}): {reason}")

        text = _THINK_RE.sub("", (response.json().get("message") or {}).get("content") or "").strip()
        if not text:
            raise EmptyResponseError(f"Ollama ({model}) returned an empty response")
        return text


class OllamaProvider(LLMProvider):
    """One Ollama model, exposed as the provider ``ollama:<model>``."""

    def __init__(self, client: OllamaClient, model: str) -> None:
        self._client = client
        self._model = model
        self.name = f"{PREFIX}{model}"

    async def generate(self, request: LLMRequest) -> str:
        return await self._client.chat(self._model, request)


def provider_resolver(client: OllamaClient):
    """Return a function turning ``"ollama:<model>"`` into a provider (``None`` for other names)."""

    def resolve(name: str) -> LLMProvider | None:
        if name.startswith(PREFIX) and len(name) > len(PREFIX):
            return OllamaProvider(client, name[len(PREFIX):])
        return None

    return resolve
