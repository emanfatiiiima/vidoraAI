"""Steps 4-7 - audio, image, video and compilation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from core.services.video import CompileClip
from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import (
    CompileRequest,
    ImageRequest,
    TTSRequest,
    UrlResponse,
    VideoRequest,
    VideoResponse,
    VoicesResponse,
)

router = APIRouter(tags=["media"])


@router.post("/tts")
async def text_to_speech(body: TTSRequest, services: ServicesDep) -> dict[str, Any]:
    """Narrate text with UnrealSpeech or a local TTS engine. The answer contains ``OutputUri``."""
    return await services.tts.synthesize(body.text, body.voice, body.speed, body.pitch, body.provider)


@router.get("/tts/voices", response_model=VoicesResponse)
async def tts_voices(services: ServicesDep, provider: str = Query(default="unrealspeech")) -> VoicesResponse:
    """Voices offered by a voice-over provider."""
    return VoicesResponse.model_validate({"voices": services.tts.voices(provider)})


@router.post("/generate-image", response_model=UrlResponse)
async def generate_image(body: ImageRequest, services: ServicesDep) -> UrlResponse:
    """Generate an image for a scene prompt with the provider the user picked (if any)."""
    return UrlResponse(url=await services.images.generate(body.prompt, body.provider))


@router.post("/generate-video", response_model=VideoResponse)
async def generate_video(body: VideoRequest, services: ServicesDep) -> VideoResponse:
    """Animate a scene image into a clip with a local video model (simulated without ``provider``)."""
    result = await services.video.generate_clip(body.image_url, body.prompt, body.provider)
    return VideoResponse(url=result.url, status=result.status)


@router.post("/compile-video", response_model=VideoResponse)
async def compile_video(body: CompileRequest, services: ServicesDep) -> VideoResponse:
    """Stitch scene clips and narration into the final video (simulated without ``provider``)."""
    clips = [CompileClip(video_url=s.video_url, text=s.text) for s in body.scenes]
    result = await services.video.compile(clips, body.audio_url, body.provider)
    return VideoResponse(url=result.url, status=result.status)
