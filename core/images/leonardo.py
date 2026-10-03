"""
Leonardo.ai image generation client.

Leonardo generates images asynchronously, so one image takes two steps:

1. ``POST /generations``          -> starts a job and returns its ``generationId``
2. ``GET  /generations/{id}``     -> polled until the job is ``COMPLETE``

API reference: https://docs.leonardo.ai/reference
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

LEONARDO_API_URL = "https://cloud.leonardo.ai/api/rest/v1"

# Vertical 9:16 frames, matching the other providers (short-form video).
# Leonardo requires both sides to be multiples of 8.
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 1344

# Polling: check every 2s, give up after 2 minutes.
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_POLL_TIMEOUT_SECONDS = 120.0


class LeonardoClient:
    """Thin async wrapper around the Leonardo.ai REST API.

    It only knows about Leonardo: it returns the hosted URL of the generated
    image and raises :class:`ExternalServiceError` when anything goes wrong.
    """

    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        api_key: str,
        model_id: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        poll_timeout_seconds: float = DEFAULT_POLL_TIMEOUT_SECONDS,
    ) -> None:
        self._http = http
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        self._model_id = model_id
        self._width = width
        self._height = height
        self._poll_interval = poll_interval_seconds
        self._poll_timeout = poll_timeout_seconds

    async def generate(self, prompt: str) -> str:
        """Generate one image for ``prompt`` and return its hosted URL.

        Raises:
            ExternalServiceError: Leonardo rejected the request, the job
                failed, or it did not finish within the poll timeout.
        """
        generation_id = await self._start_generation(prompt)
        logger.info("Leonardo generation %s started, waiting for it to finish...", generation_id)
        return await self._wait_for_image(generation_id)

    # ------------------------------------------------------------------ #
    # API steps
    # ------------------------------------------------------------------ #
    async def _start_generation(self, prompt: str) -> str:
        """Step 1: create the generation job and return its id."""
        payload = {
            "prompt": prompt,
            "modelId": self._model_id,
            "width": self._width,
            "height": self._height,
            "num_images": 1,
        }
        data = await self._request("POST", "/generations", json=payload)
        generation_id = (data.get("sdGenerationJob") or {}).get("generationId")
        if not generation_id:
            raise ExternalServiceError("Leonardo did not return a generation id", details=data)
        return generation_id

    async def _wait_for_image(self, generation_id: str) -> str:
        """Step 2: poll the job until it completes and return the first image URL."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._poll_timeout

        while True:
            data = await self._request("GET", f"/generations/{generation_id}")
            generation = data.get("generations_by_pk") or {}
            status = generation.get("status")

            if status == "COMPLETE":
                images = generation.get("generated_images") or []
                if images and images[0].get("url"):
                    logger.info("Leonardo generation %s succeeded.", generation_id)
                    return images[0]["url"]
                raise ExternalServiceError("Leonardo finished without an image", details=generation)

            if status == "FAILED":
                raise ExternalServiceError("Leonardo image generation failed", details=generation)

            # Still PENDING - wait and try again, unless we ran out of time.
            if loop.time() >= deadline:
                raise ExternalServiceError(
                    f"Leonardo image generation timed out after {self._poll_timeout:.0f}s",
                    details={"generationId": generation_id},
                )
            await asyncio.sleep(self._poll_interval)

    # ------------------------------------------------------------------ #
    # HTTP helper
    # ------------------------------------------------------------------ #
    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Send one authenticated request and return the JSON body.

        Network errors and non-2xx responses become :class:`ExternalServiceError`
        (keeping the upstream status, so a 429 reaches the UI as "quota reached").
        """
        try:
            response = await self._http.request(
                method, f"{LEONARDO_API_URL}{path}", headers=self._headers, **kwargs
            )
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Could not reach Leonardo", details=str(exc)) from exc

        if response.is_error:
            try:
                details: Any = response.json()
            except ValueError:
                details = response.text
            logger.warning("Leonardo error (%s): %s", response.status_code, details)
            raise ExternalServiceError(
                "Leonardo rejected the request",
                upstream_status=response.status_code,
                details=details,
            )
        return response.json()
