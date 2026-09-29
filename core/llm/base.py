"""
Provider-agnostic types for text generation.

Every LLM provider implements :class:`LLMProvider`. The rest of the core only
talks to this interface (usually through :class:`core.llm.router.LLMRouter`),
so adding a new provider - e.g. a local Ollama model - only requires one new
class, no changes to the services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """A single text-generation request."""

    prompt: str
    system_prompt: str | None = None
    # When True the provider is asked to return strict JSON (if it supports it).
    json_mode: bool = False


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """The generated text plus the name of the provider that produced it."""

    text: str
    provider: str


class LLMProvider(ABC):
    """Interface implemented by every text-generation provider."""

    #: Short, unique name (used in logs, config and API responses).
    name: str

    @abstractmethod
    async def generate(self, request: LLMRequest) -> str:
        """Generate text for ``request``.

        Implementations should raise on any failure (network error, quota,
        empty answer, ...) so the router can fall back to the next provider.
        """
