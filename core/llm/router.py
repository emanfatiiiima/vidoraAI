"""
LLM router with automatic fallback.

The router holds an ordered list of providers and tries them one by one until
one succeeds. This gives the app resilience against quota limits and outages
of a single provider.

Callers may also pin a single provider by name (e.g. when the user picks one
in the UI). In that case no fallback happens: if it fails, the error is raised.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from core.exceptions import (
    AllProvidersFailedError,
    ProviderFailedError,
    ProviderNotConfiguredError,
)
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
        provider: str | None = None,
    ) -> LLMResponse:
        """Generate text, falling back through the providers on failure.

        When ``provider`` is given, only that provider is used (no fallback).

        Raises:
            AllProvidersFailedError: no provider is configured or all failed.
            ProviderNotConfiguredError: ``provider`` has no API key configured.
            ProviderFailedError: the selected ``provider`` failed.
        """
        request = LLMRequest(prompt=prompt, system_prompt=system_prompt, json_mode=json_mode)
        if provider is not None:
            return await self._generate_with(provider, request)

        errors: dict[str, str] = {}

        for candidate in self._providers:
            logger.info("Attempting text generation with %s...", candidate.name)
            try:
                text = await candidate.generate(request)
            except Exception as exc:  # noqa: BLE001 - any provider failure triggers fallback
                logger.warning("%s failed: %s", candidate.name, exc)
                errors[candidate.name] = str(exc)
                continue
            return LLMResponse(text=text, provider=candidate.name)

        raise AllProvidersFailedError(
            "All AI providers failed or are not configured.",
            details=errors or None,
        )

    async def _generate_with(self, name: str, request: LLMRequest) -> LLMResponse:
        """Generate with the single provider called ``name`` (no fallback)."""
        selected = next((p for p in self._providers if p.name == name), None)
        if selected is None:
            raise ProviderNotConfiguredError(
                f"The {name} provider is not configured.", details={"provider": name}
            )
        logger.info("Attempting text generation with %s (user selected)...", name)
        try:
            text = await selected.generate(request)
        except Exception as exc:  # noqa: BLE001 - reported to the user instead of falling back
            logger.warning("%s failed: %s", name, exc)
            raise ProviderFailedError(
                f"The {name} provider failed.", details={"provider": name, "reason": str(exc)}
            ) from exc
        return LLMResponse(text=text, provider=name)
