"""
Scene image generation (Step 5 of the video pipeline).

Providers are tried in this order:

1. Gemini native image generation
2. OpenAI DALL-E 3
3. Pollinations.ai (free, no key needed) - always available as a last resort
"""

from __future__ import annotations

import base64
import logging
import random
from urllib.parse import quote, urlencode

from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
GEMINI_ASPECT_RATIO = "9:16"
DALLE_SIZE = "1024x1792"


class ImageService:
    """Generates an image for a scene prompt and returns a displayable URL."""

    def __init__(
        self,
        *,
        gemini: genai.Client | None,
        gemini_model: str,
        openai: AsyncOpenAI | None,
        openai_model: str,
    ) -> None:
        self._gemini = gemini
        self._gemini_model = gemini_model
        self._openai = openai
        self._openai_model = openai_model

    async def generate(self, prompt: str) -> str:
        """Return an image URL (http(s) or ``data:`` URI) for ``prompt``.

        Never raises: falls back to Pollinations when paid providers fail.
        """
        for attempt in (self._try_gemini, self._try_openai):
            url = await attempt(prompt)
            if url:
                return url

        logger.info("Using Pollinations flux engine for scene image fallback.")
        return self._pollinations_url(prompt)

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
