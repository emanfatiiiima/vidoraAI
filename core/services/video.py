"""
Scene video generation and final compilation (Steps 6-7 of the video pipeline).

IMPORTANT: both operations are currently **simulated**. They wait a few
seconds (to mimic AI compute time) and return placeholder URLs so the full UI
flow can be developed and tested end-to-end.

To make them real:
- ``generate_clip``: call an image-to-video API (Luma Dream Machine, Runway,
  Kling, ...) with ``image_url`` + ``prompt`` and return the resulting clip URL.
- ``compile``: run an FFmpeg job (or cloud editor) that stitches the scene
  clips together and overlays ``audio_url``, then return the final video URL.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass

logger = logging.getLogger(__name__)

PLACEHOLDER_CLIP_URL = "https://v.liquidpro.io/static/motion_sample_1.mp4"
PLACEHOLDER_FINAL_URL = "https://v.liquidpro.io/static/final_demo_assembly.mp4"


@dataclass(frozen=True, slots=True)
class VideoResult:
    """Result of a video operation."""

    url: str
    status: str


class VideoService:
    """Turns scene images into clips and clips into the final video."""

    def __init__(
        self,
        *,
        clip_delay_seconds: float = 3.0,
        compile_delay_seconds: float = 5.0,
    ) -> None:
        # Delays are configurable so tests can run instantly.
        self._clip_delay = clip_delay_seconds
        self._compile_delay = compile_delay_seconds

    async def generate_clip(self, image_url: str | None, prompt: str | None) -> VideoResult:
        """Animate a scene image into a short video clip (simulated)."""
        logger.info("Generating video motion for: %.80s", prompt)
        await asyncio.sleep(self._clip_delay)
        return VideoResult(url=PLACEHOLDER_CLIP_URL, status="completed")

    async def compile(self, clip_urls: Sequence[str | None], audio_url: str | None) -> VideoResult:
        """Stitch all scene clips together with the narration (simulated)."""
        logger.info("Compiling %d clips with audio: %s", len(clip_urls), audio_url)
        await asyncio.sleep(self._compile_delay)
        return VideoResult(url=PLACEHOLDER_FINAL_URL, status="success")
