"""
LLM router with automatic fallback.

The router holds an ordered list of providers and tries them one by one until
one succeeds. This gives the app resilience against quota limits and outages
of a single provider.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from core.exceptions import AllProvidersFailedError
from core.llm.base import LLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class LLMRouter:
    """Tries each provider in order and returns the first successful answer."""

    def __init__(self, providers: Sequence[LLMProvider]) -> None:
        self._providers = list(providers)

    @property
    def provider_names(self) -> list[str]:
        """Names of the configured providers, in the order they are tried."""
        return [p.name for p in self._providers]

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate text, falling back through the providers on failure.

        Raises:
            AllProvidersFailedError: no provider is configured or all failed.
        """
        request = LLMRequest(prompt=prompt, system_prompt=system_prompt, json_mode=json_mode)
        errors: dict[str, str] = {}

        for provider in self._providers:
            logger.info("Attempting text generation with %s...", provider.name)
            try:
                text = await provider.generate(request)
            except Exception as exc:  # noqa: BLE001 - any provider failure triggers fallback
                logger.warning("%s failed: %s", provider.name, exc)
                errors[provider.name] = str(exc)
                continue
            return LLMResponse(text=text, provider=provider.name)

        raise AllProvidersFailedError(
            "All AI providers failed or are not configured.",
            details=errors or None,
        )
