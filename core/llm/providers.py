"""
Concrete LLM providers: Google Gemini, OpenAI and Groq.

OpenAI and Groq share the same "chat completions" API shape, so they both
extend :class:`_ChatCompletionsProvider`.
"""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types as genai_types
from groq import AsyncGroq
from openai import AsyncOpenAI

from core.llm.base import LLMProvider, LLMRequest


class EmptyResponseError(RuntimeError):
    """Raised when a provider returns no text, so the router tries the next one."""


# ---------------------------------------------------------------------- #
# Gemini
# ---------------------------------------------------------------------- #
class GeminiProvider(LLMProvider):
    """Google Gemini via the official ``google-genai`` SDK."""

    name = "gemini"

    def __init__(self, client: genai.Client, model: str) -> None:
        self._client = client
        self._model = model

    async def generate(self, request: LLMRequest) -> str:
        config = genai_types.GenerateContentConfig(
            system_instruction=request.system_prompt or None,
            response_mime_type="application/json" if request.json_mode else None,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=request.prompt,
            config=config,
        )
        if not response.text:
            raise EmptyResponseError("Gemini returned an empty response")
        return response.text


# ---------------------------------------------------------------------- #
# OpenAI-compatible (OpenAI, Groq)
# ---------------------------------------------------------------------- #
class _ChatCompletionsProvider(LLMProvider):
    """Shared logic for providers exposing the OpenAI chat-completions API."""

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    @staticmethod
    def _build_messages(request: LLMRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    async def generate(self, request: LLMRequest) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(request),
        }
        if request.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content
        if not text:
            raise EmptyResponseError(f"{self.name} returned an empty response")
        return text


class OpenAIProvider(_ChatCompletionsProvider):
    """OpenAI (GPT models)."""

    name = "openai"

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        super().__init__(client, model)


class GroqProvider(_ChatCompletionsProvider):
    """Groq (hosted open-source models such as Llama)."""

    name = "groq"

    def __init__(self, client: AsyncGroq, model: str) -> None:
        super().__init__(client, model)
