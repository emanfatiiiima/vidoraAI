"""
Final video compilation with FFmpeg, MoviePy or Kdenlive's MLT renderer.

All three produce the same result:

1. every scene gets a share of the narration, proportional to the number of
   words it narrates (so the visuals follow the voice);
2. each clip is scaled/cropped to the output size and looped "ping-pong"
   (forward, then reversed) until its slot is filled - smoother than a hard loop;
3. the scenes are joined, the narration is laid on top and the result is
   encoded as H.264/AAC MP4 with ``faststart`` (plays instantly in the browser).

Kdenlive additionally leaves a ``.mlt`` project next to the video, which you
can open in Kdenlive to fine-tune the edit by hand.

The functions here are blocking; :class:`core.services.VideoService` runs them
in a thread.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import quoteattr

# Shortest time a scene stays on screen, in seconds.
MIN_SCENE_SECONDS = 1.5
# Used when there is no narration.
DEFAULT_SCENE_SECONDS = 5.0
RUN_TIMEOUT_SECONDS = 3600
_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


class CompileError(RuntimeError):
    """Compilation failed (message is user-facing)."""


@dataclass(frozen=True, slots=True)
class RenderSpec:
    width: int = 1080
    height: int = 1920
    fps: int = 30


@dataclass(slots=True)
class CompileJob:
    clips: list[Path]
    #: Relative screen time of each clip (e.g. word count of its narration).
    weights: list[float]
    audio: Path | None
    output: Path
    #: Scratch folder for intermediate files (deleted afterwards by the caller).
    work_dir: Path


def scene_durations(total: float | None, weights: list[float]) -> list[float]:
    """Split ``total`` seconds between scenes proportionally to ``weights``."""
    if not weights:
        return []
    if not total:
        return [DEFAULT_SCENE_SECONDS] * len(weights)
    safe = [max(w, 1.0) for w in weights]
    raw = [total * w / sum(safe) for w in safe]
    # Lift very short scenes to the minimum and take that time from the longest ones.
    short = [max(MIN_SCENE_SECONDS - d, 0.0) for d in raw]
    durations = [max(d, MIN_SCENE_SECONDS) for d in raw]
    debt = sum(short)
    while debt > 1e-6:
        longest = max(range(len(durations)), key=durations.__getitem__)
        take = min(debt, max(durations[longest] - MIN_SCENE_SECONDS, 0.0))
        if take <= 0:
            break
        durations[longest] -= take
        debt -= take
    return durations


def _tail(result: subprocess.CompletedProcess) -> str:
    lines = (result.stderr or result.stdout or "").strip().splitlines()
    return " | ".join(lines[-4:]) or f"exit code {result.returncode}"


# ---------------------------------------------------------------------- #
# FFmpeg
# ---------------------------------------------------------------------- #
class FFmpegCompiler:
    """Pure FFmpeg pipeline. Also used by Kdenlive to prepare the clips."""

    name = "ffmpeg"

    def __init__(self, ffmpeg_path: str, spec: RenderSpec) -> None:
        self._ffmpeg = ffmpeg_path
        self.spec = spec

    @property
    def binary(self) -> str | None:
        return shutil.which(self._ffmpeg)

    def problem(self) -> str | None:
        if self.binary is None:
            return f"FFmpeg not found ('{self._ffmpeg}'). Install it and add it to PATH (LOCAL_SETUP.md, step 1)."
        return None

    def run(self, *args: str) -> None:
        result = subprocess.run([self.binary or self._ffmpeg, "-hide_banner", "-y", *args],
                                capture_output=True, text=True, timeout=RUN_TIMEOUT_SECONDS)
        if result.returncode != 0:
            raise CompileError(f"FFmpeg failed: {_tail(result)}")

    def duration(self, path: Path) -> float | None:
        """Media duration in seconds (parsed from ``ffmpeg -i``; no ffprobe needed)."""
        result = subprocess.run([self.binary or self._ffmpeg, "-hide_banner", "-i", str(path)],
                                capture_output=True, text=True, timeout=60)
        match = _DURATION_RE.search(result.stderr)
        if not match:
            return None
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    def prepare_segments(self, job: CompileJob, segment_dir: Path | None = None) -> tuple[list[Path], list[float]]:
        """Normalise every clip to the output size/fps and the length of its scene.

        Segments are written to ``segment_dir`` (default: the job's scratch folder).
        """
        segment_dir = segment_dir or job.work_dir
        total = self.duration(job.audio) if job.audio else None
        durations = scene_durations(total, job.weights)
        s = self.spec
        fit = (f"scale={s.width}:{s.height}:force_original_aspect_ratio=increase,"
               f"crop={s.width}:{s.height},setsar=1,fps={s.fps},format=yuv420p")
        segments = []
        for i, (clip, seconds) in enumerate(zip(job.clips, durations, strict=True)):
            bounce = job.work_dir / f"bounce_{i}.mp4"
            segment = segment_dir / f"scene_{i + 1}.mp4"
            # Forward + reversed copy = a seamless "ping-pong" loop.
            self.run("-i", str(clip), "-filter_complex",
                     f"[0:v]{fit},split[f][b];[b]reverse[r];[f][r]concat=n=2:v=1:a=0[v]",
                     "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(bounce))
            self.run("-stream_loop", "-1", "-i", str(bounce), "-t", f"{seconds:.3f}", "-an",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                     "-r", str(s.fps), str(segment))
            segments.append(segment)
        return segments, durations

    def compile(self, job: CompileJob) -> None:
        segments, _ = self.prepare_segments(job)
        concat_list = job.work_dir / "segments.txt"
        concat_list.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in segments), encoding="utf-8"
        )
        args = ["-f", "concat", "-safe", "0", "-i", str(concat_list)]
        if job.audio:
            args += ["-i", str(job.audio), "-map", "0:v:0", "-map", "1:a:0",
                     "-c:a", "aac", "-b:a", "192k", "-shortest"]
        self.run(*args, "-c:v", "copy", "-movflags", "+faststart", str(job.output))


# ---------------------------------------------------------------------- #
# MoviePy
# ---------------------------------------------------------------------- #
class MoviePyCompiler:
    """Same edit done in Python with MoviePy 2 (uses its bundled ffmpeg)."""

    name = "moviepy"

    def __init__(self, spec: RenderSpec) -> None:
        self.spec = spec

    def problem(self) -> str | None:
        try:
            import moviepy  # noqa: F401
        except ImportError:
            return "MoviePy is not installed in the backend venv. Run: pip install -r requirements.txt"
        return None

    def compile(self, job: CompileJob) -> None:
        from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips, vfx

        s = self.spec
        audio = AudioFileClip(str(job.audio)) if job.audio else None
        durations = scene_durations(audio.duration if audio else None, job.weights)
        opened = []
        try:
            segments = []
            for clip_path, seconds in zip(job.clips, durations, strict=True):
                clip = VideoFileClip(str(clip_path), audio=False)
                opened.append(clip)
                # Integer sizes: H.264 rejects odd dimensions caused by float rounding.
                scale = max(s.width / clip.w, s.height / clip.h)
                width, height = max(s.width, math.ceil(clip.w * scale)), max(s.height, math.ceil(clip.h * scale))
                clip = clip.resized(new_size=(width, height))
                clip = clip.cropped(x1=(width - s.width) // 2, y1=(height - s.height) // 2,
                                    width=s.width, height=s.height)
                bounce = concatenate_videoclips([clip, clip.with_effects([vfx.TimeMirror()])])
                segments.append(bounce.with_effects([vfx.Loop(duration=seconds)]))
            final = concatenate_videoclips(segments)
            if audio:
                final = final.with_audio(audio).with_duration(min(final.duration, audio.duration))
            final.write_videofile(
                str(job.output), fps=s.fps, codec="libx264", audio_codec="aac", preset="veryfast",
                threads=os.cpu_count() or 4, logger=None,
                ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-crf", "18"],
            )
        except Exception as exc:  # noqa: BLE001
            raise CompileError(f"MoviePy failed: {exc}") from exc
        finally:
            for clip in opened:
                clip.close()
            if audio:
                audio.close()


# ---------------------------------------------------------------------- #
# Kdenlive (MLT)
# ---------------------------------------------------------------------- #
_MELT_CANDIDATES = (
    r"C:\Program Files\kdenlive\bin\melt.exe",
    "/usr/bin/melt",
    "/Applications/kdenlive.app/Contents/MacOS/melt",
)


class KdenliveCompiler:
    """Builds an MLT project (Kdenlive's engine) and renders it with ``melt``."""

    name = "kdenlive"

    def __init__(self, ffmpeg: FFmpegCompiler, melt_path: str | None) -> None:
        self._ffmpeg = ffmpeg
        self._melt_path = melt_path

    @property
    def melt(self) -> str | None:
        if self._melt_path:
            return self._melt_path if Path(self._melt_path).is_file() else shutil.which(self._melt_path)
        return shutil.which("melt") or next((p for p in _MELT_CANDIDATES if Path(p).is_file()), None)

    def problem(self) -> str | None:
        if self._ffmpeg.problem():
            return self._ffmpeg.problem()
        if self.melt is None:
            return "Kdenlive's 'melt' renderer not found. Install Kdenlive or set MELT_PATH (LOCAL_SETUP.md, step 1)."
        return None

    def compile(self, job: CompileJob) -> None:
        # The project and its media are kept next to the video so it can be opened in Kdenlive.
        keep = job.output.with_name(f"{job.output.stem}_kdenlive")
        keep.mkdir(parents=True, exist_ok=True)
        segments, durations = self._ffmpeg.prepare_segments(job, keep)
        audio = None
        if job.audio:
            audio = keep / f"narration{job.audio.suffix}"
            shutil.copyfile(job.audio, audio)
        project = keep / "project.mlt"
        project.write_text(self._project_xml(segments, durations, audio), encoding="utf-8")

        melt = self.melt or "melt"
        result = subprocess.run(
            [melt, str(project), "-consumer", f"avformat:{job.output}", "vcodec=libx264", "acodec=aac",
             "ab=192k", "crf=18", "preset=veryfast", "movflags=+faststart", "real_time=-1"],
            capture_output=True, text=True, timeout=RUN_TIMEOUT_SECONDS,
            # On Windows melt finds its MLT plugins relative to its own folder.
            cwd=str(Path(melt).parent) if Path(melt).is_file() else None,
        )
        if result.returncode != 0 or not job.output.is_file():
            raise CompileError(f"Kdenlive/melt failed: {_tail(result)}")

    def _project_xml(self, segments: list[Path], durations: list[float], audio: Path | None) -> str:
        s = self._ffmpeg.spec
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<mlt LC_NUMERIC="C" version="7.0.0" title="VidoraAI render">',
            f'  <profile description="VidoraAI {s.width}x{s.height}" width="{s.width}" height="{s.height}" '
            f'progressive="1" sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="{s.width}" '
            f'display_aspect_den="{s.height}" frame_rate_num="{s.fps}" frame_rate_den="1" colorspace="709"/>',
        ]
        for i, segment in enumerate(segments):
            lines.append(f'  <producer id="scene{i}"><property name="resource">{_xml(segment)}</property></producer>')
        if audio:
            lines.append(f'  <producer id="narration"><property name="resource">{_xml(audio)}</property></producer>')

        lines.append('  <playlist id="video_track">')
        for i, seconds in enumerate(durations):
            lines.append(f'    <entry producer="scene{i}" in="0" out="{max(round(seconds * s.fps) - 1, 0)}"/>')
        lines.append("  </playlist>")
        if audio:
            lines += ['  <playlist id="audio_track">', '    <entry producer="narration"/>', "  </playlist>"]

        lines.append('  <tractor id="main">')
        lines.append('    <track producer="video_track"/>')
        if audio:
            lines += [
                '    <track producer="audio_track" hide="video"/>',
                '    <transition mlt_service="mix"><property name="a_track">0</property>'
                '<property name="b_track">1</property><property name="always_active">1</property>'
                '<property name="sum">1</property></transition>',
            ]
        lines += ["  </tractor>", "</mlt>", ""]
        return "\n".join(lines)


def _xml(path: Path) -> str:
    return quoteattr(path.resolve().as_posix())[1:-1]
