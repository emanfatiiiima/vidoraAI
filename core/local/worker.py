"""
Client for the local GPU worker (``python -m local_ai``, see ``local_ai/server.py``).

The worker runs in its own venv with PyTorch, so the backend never imports any
model library: it sends a job over HTTP and gets the finished file back.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

from core.exceptions import ProviderFailedError, ProviderNotConfiguredError
from local_ai.catalog import ENGINES

logger = logging.getLogger(__name__)

START_HINT = "Start it with: local_ai\\.venv\\Scripts\\python -m local_ai (LOCAL_SETUP.md, step 10)."


class LocalWorkerClient:
    """Sends TTS / image / video jobs to the GPU worker."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, timeout_seconds: float) -> None:
        self._http = http
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def health(self) -> dict[str, Any]:
        """The worker's ``/health`` (engine id -> ``{available, reason}``).

        Raises:
            ProviderNotConfiguredError: the worker is not running.
        """
        try:
            response = await self._http.get(f"{self.base_url}/health", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderNotConfiguredError(
                f"The local AI worker is not running at {self.base_url}.",
                details={"hint": START_HINT},
            ) from exc

    async def tts(self, engine: str, text: str, voice: str | None, speed: float) -> bytes:
        return await self._job("/tts", engine, {"text": text, "voice": voice, "speed": speed})

    async def image(self, engine: str, prompt: str) -> bytes:
        return await self._job("/image", engine, {"prompt": prompt})

    async def video(self, engine: str, image: bytes, prompt: str) -> bytes:
        payload = {"imageBase64": base64.b64encode(image).decode("ascii"), "prompt": prompt}
        return await self._job("/video", engine, payload)

    async def _job(self, path: str, engine: str, payload: dict[str, Any]) -> bytes:
        label = ENGINES[engine].label
        logger.info("Sending %s job to the local worker (%s)...", engine, path)
        try:
            response = await self._http.post(
                f"{self.base_url}{path}", json={"engine": engine, **payload}, timeout=self._timeout
            )
        except httpx.TimeoutException as exc:
            raise ProviderFailedError(
                f"{label} did not finish in time.",
                details={"provider": engine, "reason": "Timed out - try a lighter model."},
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderNotConfiguredError(
                f"The local AI worker is not running at {self.base_url}.",
                details={"provider": engine, "hint": START_HINT},
            ) from exc

        if response.is_error:
            try:
                reason = response.json().get("error") or response.text
            except ValueError:
                reason = response.text
            if response.status_code == 503:
                raise ProviderNotConfiguredError(f"{label} is not ready.", details={"provider": engine, "hint": reason})
            raise ProviderFailedError(f"{label} failed.", details={"provider": engine, "reason": reason})
        return response.content
