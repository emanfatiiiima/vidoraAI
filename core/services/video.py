"""
Scene video generation and final compilation (Steps 6-7 of the video pipeline).

* ``generate_clip`` animates a scene image with a local image-to-video model
  (LTX-Video, Stable Video Diffusion XT, Wan 2.1 VACE, CogVideoX) on the GPU
  worker and stores the clip in the media folder.
* ``compile`` renders the final video with FFmpeg, MoviePy or Kdenlive (MLT)
  - see :mod:`core.local.compile`.

When no ``provider`` is given, both operations are **simulated** (they wait a
moment and return a sample clip), which keeps the UI flow testable without
any model installed.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from core.exceptions import InvalidInputError, ProviderFailedError, ProviderNotConfiguredError
from core.local import CompileError, CompileJob, LocalWorkerClient, MediaStore
from local_ai.catalog import COMPILERS, ENGINES, engine_ids

logger = logging.getLogger(__name__)

# Public-domain (CC0) sample clip from MDN, used when no video AI is picked.
PLACEHOLDER_CLIP_URL = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
PLACEHOLDER_FINAL_URL = PLACEHOLDER_CLIP_URL

LOCAL_VIDEO_ENGINES = engine_ids("video")
VideoProviderName = Literal["ltx-video", "svd-xt", "wan-1.3b", "cogvideox-2b"]
CompileProviderName = Literal["ffmpeg", "moviepy", "kdenlive"]


class Compiler(Protocol):
    name: str

    def problem(self) -> str | None: ...

    def compile(self, job: CompileJob) -> None: ...


@dataclass(frozen=True, slots=True)
class VideoResult:
    """Result of a video operation."""

    url: str
    status: str


@dataclass(frozen=True, slots=True)
class CompileClip:
    """One scene of the final video."""

    video_url: str | None
    #: Narration of the scene; its word count sets the scene's screen time.
    text: str = ""


class VideoService:
    """Turns scene images into clips and clips into the final video."""

    def __init__(
        self,
        *,
        clip_delay_seconds: float = 3.0,
        compile_delay_seconds: float = 5.0,
        worker: LocalWorkerClient | None = None,
        media: MediaStore | None = None,
        compilers: Sequence[Compiler] = (),
    ) -> None:
        # Delays (simulated mode only) are configurable so tests can run instantly.
        self._clip_delay = clip_delay_seconds
        self._compile_delay = compile_delay_seconds
        self._worker = worker
        self._media = media
        self._compilers = {c.name: c for c in compilers}

    def compiler_problem(self, name: str) -> str | None:
        """Why compiler ``name`` can't run, or ``None`` when it can."""
        compiler = self._compilers.get(name)
        return "Not configured on the server." if compiler is None else compiler.problem()

    # ------------------------------------------------------------------ #
    # Step 6 - scene clips
    # ------------------------------------------------------------------ #
    async def generate_clip(
        self, image_url: str | None, prompt: str | None, provider: str | None = None
    ) -> VideoResult:
        """Animate a scene image into a short video clip."""
        if provider is None:
            logger.info("Generating simulated video motion for: %.80s", prompt)
            await asyncio.sleep(self._clip_delay)
            return VideoResult(url=PLACEHOLDER_CLIP_URL, status="completed")

        if provider not in LOCAL_VIDEO_ENGINES:
            raise InvalidInputError(f"Unknown video model '{provider}'.")
        if self._worker is None or self._media is None:
            raise ProviderNotConfiguredError("The local AI worker is not configured.", details={"provider": provider})
        if not image_url:
            raise InvalidInputError("The scene has no image to animate.")

        try:
            image, _ = await self._media.read(image_url)
        except Exception as exc:  # noqa: BLE001
            raise InvalidInputError("Couldn't read the scene image. Regenerate it in Step 5.") from exc
        clip = await self._worker.video(provider, image, prompt or "")
        url = self._media.save(clip, "clips", ".mp4")
        logger.info("%s clip ready: %s", ENGINES[provider].label, url)
        return VideoResult(url=url, status="completed")

    # ------------------------------------------------------------------ #
    # Step 7 - final render
    # ------------------------------------------------------------------ #
    async def compile(
        self,
        clips: Sequence[CompileClip],
        audio_url: str | None,
        provider: str | None = None,
    ) -> VideoResult:
        """Stitch all scene clips together with the narration."""
        if provider is None:
            logger.info("Compiling %d clips (simulated) with audio: %s", len(clips), audio_url)
            await asyncio.sleep(self._compile_delay)
            return VideoResult(url=PLACEHOLDER_FINAL_URL, status="success")

        compiler = self._compilers.get(provider)
        if compiler is None or self._media is None:
            raise ProviderNotConfiguredError(f"The {provider} renderer is not configured.", details={"provider": provider})
        label = COMPILERS[provider]
        problem = compiler.problem()
        if problem:
            raise ProviderNotConfiguredError(f"{label} is not ready.", details={"provider": provider, "hint": problem})
        missing = [i for i, c in enumerate(clips, start=1) if not c.video_url]
        if not clips or missing:
            raise InvalidInputError(f"Scene(s) {', '.join(map(str, missing)) or '-'} have no clip yet.")

        work_dir = self._media.root / "work" / uuid.uuid4().hex[:12]
        work_dir.mkdir(parents=True)
        try:
            # Clips/audio may be data URIs or remote links: make them local files first.
            clip_files = [await self._media.to_file(c.video_url, f"work/{work_dir.name}", ".mp4") for c in clips]
            audio_file = await self._media.to_file(audio_url, f"work/{work_dir.name}", ".mp3") if audio_url else None
            output, url = self._media.new_file("final", ".mp4")
            job = CompileJob(
                clips=clip_files,
                weights=[float(len(c.text.split())) for c in clips],
                audio=audio_file,
                output=output,
                work_dir=work_dir,
            )
            logger.info("Rendering %d scenes with %s...", len(clips), label)
            await asyncio.to_thread(compiler.compile, job)
        except CompileError as exc:
            raise ProviderFailedError(f"{label} failed.", details={"provider": provider, "reason": str(exc)}) from exc
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

        logger.info("Final video ready: %s", url)
        return VideoResult(url=url, status="success")
