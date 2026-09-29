"""
Text-to-speech (Step 4 of the video pipeline) using UnrealSpeech.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.exceptions import ExternalServiceError, InvalidInputError, ProviderNotConfiguredError

logger = logging.getLogger(__name__)

UNREAL_SPEECH_URL = "https://api.v8.unrealspeech.com/speech"
# UnrealSpeech's /speech endpoint accepts at most 3000 characters.
MAX_TTS_CHARS = 3000
DEFAULT_VOICE = "Sierra"
DEFAULT_SPEED = 0.0  # range -1.0 .. 1.0
DEFAULT_PITCH = 1.0  # range 0.5 .. 1.5


class TextToSpeechService:
    """Converts a script into a narrated MP3 using UnrealSpeech."""

    def __init__(self, http: httpx.AsyncClient, api_key: str | None) -> None:
        self._http = http
        self._api_key = api_key

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
        pitch: float | None = None,
    ) -> dict[str, Any]:
        """Generate speech and return UnrealSpeech's JSON response.

        The response contains ``OutputUri`` - a URL of the generated MP3.

        Raises:
            ProviderNotConfiguredError: ``UNREAL_SPEECH_API_KEY`` is missing.
            InvalidInputError: ``text`` is empty.
            ExternalServiceError: UnrealSpeech returned an error.
        """
        if not self._api_key:
            raise ProviderNotConfiguredError("UNREAL_SPEECH_API_KEY not configured")
        if not text:
            raise InvalidInputError("Text is required")

        # Trim to the API limit instead of failing.
        safe_text = text if len(text) <= MAX_TTS_CHARS else text[: MAX_TTS_CHARS - 1]

        payload = {
            "Text": safe_text,
            "VoiceId": voice or DEFAULT_VOICE,
            "Bitrate": "192k",
            "OutputFormat": "uri",
            "AudioFormat": "mp3",
            "sync": True,  # must be True to receive OutputUri immediately
            "Speed": speed or DEFAULT_SPEED,
            "Pitch": pitch or DEFAULT_PITCH,
        }

        try:
            response = await self._http.post(
                UNREAL_SPEECH_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Failed to generate speech", details=str(exc)) from exc

        if response.is_error:
            details = _safe_json(response)
            logger.error("TTS error (%s): %s", response.status_code, details)
            raise ExternalServiceError(
                "Failed to generate speech",
                upstream_status=response.status_code,
                details=details,
            )

        data = response.json()
        logger.info("TTS success: %s", data.get("OutputUri"))
        return data


def _safe_json(response: httpx.Response) -> Any:
    """Return the JSON body of ``response`` or its raw text if it isn't JSON."""
    try:
        return response.json()
    except ValueError:
        return response.text
