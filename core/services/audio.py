"""
Text-to-speech (Step 4 of the video pipeline).

* ``unrealspeech`` (cloud) - returns UnrealSpeech's JSON with a hosted ``OutputUri``.
* local engines (Kokoro, Piper, XTTS-v2, MeloTTS, Bark) - rendered by the GPU
  worker, stored in the media folder; the answer has the same ``OutputUri`` shape.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.exceptions import ExternalServiceError, InvalidInputError, ProviderNotConfiguredError
from core.local import LocalWorkerClient, MediaStore
from local_ai.catalog import ENGINES, engine_ids

logger = logging.getLogger(__name__)

UNREAL_SPEECH_URL = "https://api.v8.unrealspeech.com/speech"
# UnrealSpeech's /speech endpoint accepts at most 3000 characters.
MAX_TTS_CHARS = 3000
DEFAULT_VOICE = "Sierra"
DEFAULT_SPEED = 0.0  # range -1.0 .. 1.0
DEFAULT_PITCH = 1.0  # range 0.5 .. 1.5

#: UnrealSpeech voices shown in Step 4.
UNREAL_VOICES = [
    {"id": "Sierra", "name": "Sierra", "desc": "Professional & balanced", "type": "Female"},
    {"id": "Mateo", "name": "Mateo", "desc": "Deep & authoritative", "type": "Male"},
    {"id": "Scarlett", "name": "Scarlett", "desc": "Expressive & warm", "type": "Female"},
    {"id": "Dan", "name": "Dan", "desc": "Friendly & casual", "type": "Male"},
    {"id": "Liv", "name": "Liv", "desc": "Young & energetic", "type": "Female"},
    {"id": "Will", "name": "Will", "desc": "News anchor style", "type": "Male"},
]
LOCAL_TTS_ENGINES = engine_ids("tts")


class TextToSpeechService:
    """Converts a script into narration with UnrealSpeech or a local TTS engine."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        api_key: str | None,
        worker: LocalWorkerClient | None = None,
        media: MediaStore | None = None,
    ) -> None:
        self._http = http
        self._api_key = api_key
        self._worker = worker
        self._media = media

    @staticmethod
    def voices(provider: str) -> list[dict[str, str]]:
        """Voices offered for ``provider`` (empty for an unknown provider)."""
        if provider == "unrealspeech":
            return UNREAL_VOICES
        if provider in LOCAL_TTS_ENGINES:
            return [
                {"id": v.id, "name": v.name, "desc": v.desc, "type": v.type} for v in ENGINES[provider].voices
            ]
        return []

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
        pitch: float | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Generate speech and return ``{"OutputUri": <audio url>, ...}``.

        ``provider`` is ``"unrealspeech"`` (default) or a local engine id.
        ``speed`` uses UnrealSpeech's -1..1 scale for every provider.

        The response contains ``OutputUri`` - a URL of the generated MP3.

        Raises:
            ProviderNotConfiguredError: ``UNREAL_SPEECH_API_KEY`` is missing.
            InvalidInputError: ``text`` is empty.
            ExternalServiceError: UnrealSpeech returned an error.
        """
        if provider in LOCAL_TTS_ENGINES:
            return await self._synthesize_local(provider, text, voice, speed)
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


    async def _synthesize_local(
        self, engine: str, text: str, voice: str | None, speed: float | None
    ) -> dict[str, Any]:
        if self._worker is None or self._media is None:
            raise ProviderNotConfiguredError("The local AI worker is not configured.", details={"provider": engine})
        if not text.strip():
            raise InvalidInputError("Text is required")
        # -1..1 slider -> 0.7x..1.3x speaking rate.
        rate = 1.0 + 0.3 * max(-1.0, min(1.0, speed or DEFAULT_SPEED))
        audio = await self._worker.tts(engine, text, voice, rate)
        url = self._media.save(audio, "audio", ".wav")
        logger.info("Local TTS (%s) success: %s", engine, url)
        return {"OutputUri": url, "provider": engine}


def _safe_json(response: httpx.Response) -> Any:
    """Return the JSON body of ``response`` or its raw text if it isn't JSON."""
    try:
        return response.json()
    except ValueError:
        return response.text
