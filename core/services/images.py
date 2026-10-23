"""
Scene image generation (Step 5 of the video pipeline).

There are two ways a provider is chosen:

* **User selected** - the user picked an image AI before the project started
  and the UI sends it as ``provider``. Only that provider is used and its
  errors are raised, so the UI can ask the user to pick another one. Local
  models (SD 1.5, SDXL Turbo, SDXL, FLUX.1-schnell) run on the GPU worker.
* **Automatic** - no provider sent. Tried in this order:

  1. Gemini native image generation
  2. OpenAI DALL-E 3
  3. Pollinations.ai (free, no key needed) - always available as a last resort

Images are returned as ``data:`` URIs whenever possible, so the browser can show
them without hitting the image host again (free hosts rate-limit parallel
requests) and the project export never depends on a link that may expire.
"""

from __future__ import annotations

import base64
import logging
import random
from collections.abc import Awaitable, Callable
from typing import Literal
from urllib.parse import quote, urlencode

import httpx
from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI

from core.exceptions import (
    CoreError,
    InvalidAIResponseError,
    ProviderFailedError,
    ProviderNotConfiguredError,
)
from core.images import LeonardoClient
from core.local import LocalWorkerClient
from core.utils import fetch_bytes
from local_ai.catalog import engine_ids

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
GEMINI_ASPECT_RATIO = "9:16"
DALLE_SIZE = "1024x1792"

#: Image providers the user can pick in the UI (cloud + local engines).
ImageProviderName = Literal["openai", "leonardo", "gemini", "sd15", "sdxl-turbo", "sdxl", "flux-schnell"]
LOCAL_IMAGE_ENGINES = engine_ids("image")


class ImageService:
    """Generates an image for a scene prompt and returns a displayable URL."""

    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        gemini: genai.Client | None,
        gemini_model: str,
        openai: AsyncOpenAI | None,
        openai_model: str,
        leonardo: LeonardoClient | None = None,
        worker: LocalWorkerClient | None = None,
    ) -> None:
        self._http = http
        self._gemini = gemini
        self._gemini_model = gemini_model
        self._openai = openai
        self._openai_model = openai_model
        self._leonardo = leonardo
        self._worker = worker

    async def generate(self, prompt: str, provider: ImageProviderName | None = None) -> str:
        """Return an image URL (http(s) or ``data:`` URI) for ``prompt``.

        Args:
            prompt: the scene's image prompt.
            provider: the provider the user picked, or ``None`` for automatic.

        Raises (only when ``provider`` is given):
            ProviderNotConfiguredError: the provider has no API key.
            ProviderFailedError / ExternalServiceError: the provider failed.

        The automatic chain never raises: it always ends with Pollinations.
        """
        if provider is None:
            return await self._generate_automatic(prompt)
        return await self._generate_with(provider, prompt)

    # ------------------------------------------------------------------ #
    # User-selected provider (no fallback)
    # ------------------------------------------------------------------ #
    async def _generate_with(self, provider: ImageProviderName, prompt: str) -> str:
        """Generate with ``provider`` only; every error goes back to the caller."""
        if provider in LOCAL_IMAGE_ENGINES:
            if self._worker is None:
                raise ProviderNotConfiguredError(
                    "The local AI worker is not configured.", details={"provider": provider}
                )
            png = await self._worker.image(provider, prompt)
            return f"data:image/png;base64,{base64.b64encode(png).decode('ascii')}"

        # provider -> (client, generator). A ``None`` client means "no API key".
        generators: dict[str, tuple[object | None, Callable[[str], Awaitable[str]]]] = {
            "gemini": (self._gemini, self._gemini_image),
            "openai": (self._openai, self._openai_image),
            "leonardo": (self._leonardo, self._leonardo_image),
        }
        client, generator = generators[provider]
        if client is None:
            raise ProviderNotConfiguredError(
                f"The {provider} image provider is not configured.", details={"provider": provider}
            )

        logger.info("Attempting %s image generation (user selected)...", provider)
        try:
            url = await generator(prompt)
        except CoreError:
            raise  # already carries a code (and upstream status) the UI understands
        except Exception as exc:  # noqa: BLE001 - SDK errors are reported to the user
            logger.warning("%s image generation failed: %s", provider, exc)
            raise ProviderFailedError(
                f"The {provider} image provider failed.",
                details={"provider": provider, "reason": str(exc)},
            ) from exc
        # Keep the preview and the project export independent of the provider's CDN.
        return await self._to_data_uri(url)

    # ------------------------------------------------------------------ #
    # Automatic fallback chain
    # ------------------------------------------------------------------ #
    async def _generate_automatic(self, prompt: str) -> str:
        """Try Gemini, then DALL-E, then Pollinations (never raises)."""
        attempts = (("Gemini", self._gemini, self._gemini_image), ("DALL-E", self._openai, self._openai_image))
        for name, client, generator in attempts:
            if client is None:
                continue
            try:
                logger.info("Attempting %s image generation...", name)
                return await generator(prompt)
            except Exception as exc:  # noqa: BLE001 - fall through to the next provider
                logger.info("%s image generation skipped: %s", name, exc)

        logger.info("Using Pollinations flux engine for scene image fallback.")
        return await self._to_data_uri(self._pollinations_url(prompt))

    # ------------------------------------------------------------------ #
    # Provider calls - each returns a URL or raises
    # ------------------------------------------------------------------ #
    async def _gemini_image(self, prompt: str) -> str:
        """Gemini native image generation -> ``data:`` URI."""
        assert self._gemini is not None
        response = await self._gemini.aio.models.generate_content(
            model=self._gemini_model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                image_config=genai_types.ImageConfig(aspect_ratio=GEMINI_ASPECT_RATIO),
            ),
        )
        candidates = response.candidates or []
        parts = (candidates[0].content.parts or []) if candidates and candidates[0].content else []
        for part in parts:
            if part.inline_data and part.inline_data.data:
                mime = part.inline_data.mime_type or "image/png"
                encoded = base64.b64encode(part.inline_data.data).decode("ascii")
                return f"data:{mime};base64,{encoded}"
        raise InvalidAIResponseError("Gemini returned no image", details={"provider": "gemini"})

    async def _openai_image(self, prompt: str) -> str:
        """OpenAI DALL-E image generation -> hosted URL."""
        assert self._openai is not None
        response = await self._openai.images.generate(
            model=self._openai_model,
            prompt=prompt,
            n=1,
            size=DALLE_SIZE,
            quality="standard",
        )
        if response.data and response.data[0].url:
            return response.data[0].url
        raise InvalidAIResponseError("DALL-E returned no image", details={"provider": "openai"})

    async def _leonardo_image(self, prompt: str) -> str:
        """Leonardo generation -> hosted URL (API details in :mod:`core.images.leonardo`)."""
        assert self._leonardo is not None
        return await self._leonardo.generate(prompt)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    async def _to_data_uri(self, url: str) -> str:
        """Download ``url`` server-side and return it as a ``data:`` URI.

        ``data:`` URIs are returned unchanged. If the download keeps failing,
        the plain URL is returned so the browser can still try to load it.
        """
        if url.startswith("data:"):
            return url
        try:
            content, content_type = await fetch_bytes(self._http, url)
        except httpx.HTTPError as exc:
            logger.warning("Image download failed, returning URL instead: %s", exc)
            return url
        encoded = base64.b64encode(content).decode("ascii")
        return f"data:{content_type or 'image/jpeg'};base64,{encoded}"

    @staticmethod
    def _pollinations_url(prompt: str) -> str:
        """Build a Pollinations.ai URL; the image is rendered when the browser loads it."""
        query = urlencode(
            {
                "seed": random.randint(0, 999_999),
                "width": 1280,
                "height": 720,
                "nologo": "true",
                "model": "flux",
            }
        )
        return f"{POLLINATIONS_URL}{quote(prompt, safe='')}?{query}"
