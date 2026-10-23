"""
Scene image generation (Step 5 of the video pipeline).

There are two ways a provider is chosen:

* **User selected** - the UI sends ``provider``. Only that provider is used and
  its errors are raised, so the UI can ask the user to pick another one.
  Currently wired up: ``"leonardo"`` (API details in :mod:`core.images.leonardo`).
* **Automatic** - no provider (or one not wired up yet). Tried in this order:

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
from typing import Literal
from urllib.parse import quote, urlencode

import httpx
from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI

from core.exceptions import ProviderNotConfiguredError
from core.images import LeonardoClient
from core.utils import fetch_bytes

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
GEMINI_ASPECT_RATIO = "9:16"
DALLE_SIZE = "1024x1792"

#: Image providers the user can pick in the UI.
ImageProviderName = Literal["openai", "leonardo", "gemini"]


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
    ) -> None:
        self._http = http
        self._gemini = gemini
        self._gemini_model = gemini_model
        self._openai = openai
        self._openai_model = openai_model
        self._leonardo = leonardo

    async def generate(self, prompt: str, provider: ImageProviderName | None = None) -> str:
        """Return an image URL (http(s) or ``data:`` URI) for ``prompt``.

        Args:
            prompt: the scene's image prompt.
            provider: the provider the user picked, or ``None`` for automatic.
                ``"openai"`` and ``"gemini"`` still go through the automatic
                chain until they get a user-selected path of their own.

        Raises:
            ProviderNotConfiguredError: Leonardo was picked but has no API key.
            ExternalServiceError: Leonardo was picked and failed.

        The automatic chain never raises: it always ends with Pollinations.
        """
        if provider == "leonardo":
            return await self._generate_with_leonardo(prompt)
        return await self._generate_automatic(prompt)

    # ------------------------------------------------------------------ #
    # User-selected providers (no fallback)
    # ------------------------------------------------------------------ #
    async def _generate_with_leonardo(self, prompt: str) -> str:
        """Generate with Leonardo only; errors go back to the caller."""
        if self._leonardo is None:
            raise ProviderNotConfiguredError(
                "LEONARDO_API_KEY not configured", details={"provider": "leonardo"}
            )
        logger.info("Attempting Leonardo image generation (user selected)...")
        url = await self._leonardo.generate(prompt)
        # Keep the preview and the project export independent of Leonardo's CDN.
        return await self._to_data_uri(url)

    # ------------------------------------------------------------------ #
    # Automatic fallback chain
    # ------------------------------------------------------------------ #
    async def _generate_automatic(self, prompt: str) -> str:
        """Try Gemini, then DALL-E, then Pollinations (never raises)."""
        for attempt in (self._try_gemini, self._try_openai):
            url = await attempt(prompt)
            if url:
                return url

        logger.info("Using Pollinations flux engine for scene image fallback.")
        return await self._try_pollinations(prompt)

    async def _try_pollinations(self, prompt: str) -> str:
        """Pollinations image as a ``data:`` URI (the image is rendered when the URL is fetched)."""
        return await self._to_data_uri(self._pollinations_url(prompt))

    async def _try_gemini(self, prompt: str) -> str | None:
        """Gemini native image generation -> ``data:`` URI, or ``None``."""
        if self._gemini is None:
            return None
        try:
            logger.info("Attempting Gemini native image generation...")
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
                    logger.info("Gemini image generation succeeded.")
                    return f"data:{mime};base64,{encoded}"
        except Exception as exc:  # noqa: BLE001 - fall through to next provider
            logger.info("Gemini image generation skipped: %s", exc)
        return None

    async def _try_openai(self, prompt: str) -> str | None:
        """OpenAI DALL-E image generation -> hosted URL, or ``None``."""
        if self._openai is None:
            return None
        try:
            logger.info("Attempting OpenAI DALL-E image generation...")
            response = await self._openai.images.generate(
                model=self._openai_model,
                prompt=prompt,
                n=1,
                size=DALLE_SIZE,
                quality="standard",
            )
            if response.data and response.data[0].url:
                return response.data[0].url
        except Exception as exc:  # noqa: BLE001 - fall through to next provider
            logger.info("DALL-E image generation not available: %s", exc)
        return None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    async def _to_data_uri(self, url: str) -> str:
        """Download ``url`` server-side and return it as a ``data:`` URI.

        If the download keeps failing, the plain URL is returned so the browser
        can still try to load it itself.
        """
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
