"""Steps 4-7 - audio, image, video and compilation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import (
    CompileRequest,
    ImageRequest,
    TTSRequest,
    UrlResponse,
    VideoRequest,
    VideoResponse,
)

router = APIRouter(tags=["media"])


@router.post("/tts")
async def text_to_speech(body: TTSRequest, services: ServicesDep) -> dict[str, Any]:
    """Narrate text with UnrealSpeech. Returns UnrealSpeech's JSON (incl. ``OutputUri``)."""
    return await services.tts.synthesize(body.text, body.voice, body.speed, body.pitch)


@router.post("/generate-image", response_model=UrlResponse)
async def generate_image(body: ImageRequest, services: ServicesDep) -> UrlResponse:
    """Generate an image for a scene prompt with the provider the user picked (if any)."""
    return UrlResponse(url=await services.images.generate(body.prompt, body.provider))


@router.post("/generate-video", response_model=VideoResponse)
async def generate_video(body: VideoRequest, services: ServicesDep) -> VideoResponse:
    """Animate a scene image into a clip (currently simulated)."""
    result = await services.video.generate_clip(body.image_url, body.prompt)
    return VideoResponse(url=result.url, status=result.status)


@router.post("/compile-video", response_model=VideoResponse)
async def compile_video(body: CompileRequest, services: ServicesDep) -> VideoResponse:
    """Stitch scene clips and narration into the final video (currently simulated)."""
    result = await services.video.compile([s.video_url for s in body.scenes], body.audio_url)
    return VideoResponse(url=result.url, status=result.status)
