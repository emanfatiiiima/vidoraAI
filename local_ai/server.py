"""
VidoraAI local GPU worker - a small HTTP API around the local models.

Run it from the project root with the worker venv::

    local_ai\\.venv\\Scripts\\python -m local_ai

The main backend calls it (``LOCAL_AI_URL``, default http://127.0.0.1:8001).
Jobs run one at a time; each request blocks until its file is ready.

| Endpoint      | Body                                   | Returns       |
|---------------|----------------------------------------|---------------|
| GET  /health  |                                        | engine status |
| POST /tts     | {engine, text, voice?, speed?}         | audio/wav     |
| POST /image   | {engine, prompt, seed?}                | image/png     |
| POST /video   | {engine, imageBase64, prompt?, seed?}  | video/mp4     |
| POST /unload  |                                        | frees the GPU |
"""

from __future__ import annotations

import base64
import importlib.util
import logging

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from local_ai import catalog
from local_ai.runtime import (
    MELO_PYTHON,
    SLOT,
    EngineInputError,
    EngineNotReady,
    gpu_info,
    is_ready,
)

logger = logging.getLogger("local_ai")
app = FastAPI(title="VidoraAI local GPU worker")


# ---------------------------------------------------------------------- #
# Status
# ---------------------------------------------------------------------- #
def engine_problem(engine_id: str) -> str | None:
    """Why ``engine_id`` can't run, or ``None`` when it's ready (cheap: no model is loaded)."""
    engine = catalog.ENGINES[engine_id]
    if engine_id == "melo" and not MELO_PYTHON.is_file():
        return f"MeloTTS venv not found ({MELO_PYTHON}). See LOCAL_SETUP.md, step 6."
    missing = [m for m in engine.modules if importlib.util.find_spec(m) is None]
    if missing:
        return f"Python package(s) {', '.join(missing)} missing in the worker venv. See LOCAL_SETUP.md, step 4."
    if not is_ready(engine_id):
        return f"Model not downloaded yet. Run: python -m local_ai.download {engine_id}"
    return None


@app.get("/health")
def health() -> dict:
    engines = {}
    for engine_id in catalog.ENGINES:
        problem = engine_problem(engine_id)
        engines[engine_id] = {"available": problem is None, "reason": problem}
    return {"status": "ok", "gpu": gpu_info(), "loaded": SLOT.loaded, "engines": engines}


@app.post("/unload")
def unload() -> dict:
    SLOT.unload()
    return {"status": "ok"}


# ---------------------------------------------------------------------- #
# Jobs
# ---------------------------------------------------------------------- #
class TTSJob(BaseModel):
    engine: str
    text: str
    voice: str | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class ImageJob(BaseModel):
    engine: str
    prompt: str
    seed: int | None = None


class VideoJob(BaseModel):
    engine: str
    image_base64: str = Field(alias="imageBase64")
    prompt: str = ""
    seed: int | None = None


@app.post("/tts")
def tts(job: TTSJob) -> Response:
    from local_ai import tts_engines

    return _run(job.engine, "tts", "audio/wav",
                lambda: tts_engines.synthesize(job.engine, job.text, job.voice, job.speed))


@app.post("/image")
def image(job: ImageJob) -> Response:
    from local_ai import image_engines

    return _run(job.engine, "image", "image/png", lambda: image_engines.generate(job.engine, job.prompt, job.seed))


@app.post("/video")
def video(job: VideoJob) -> Response:
    from local_ai import video_engines

    image_bytes = base64.b64decode(job.image_base64)
    return _run(job.engine, "video", "video/mp4",
                lambda: video_engines.generate(job.engine, image_bytes, job.prompt, job.seed))


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def _run(engine_id: str, kind: str, media_type: str, job) -> Response:
    """Run ``job`` and turn every failure into a JSON error the backend can show to the user."""
    engine = catalog.ENGINES.get(engine_id)
    if engine is None or engine.kind != kind:
        return _error(400, f"Unknown {kind} engine '{engine_id}'.")
    problem = engine_problem(engine_id)
    if problem:
        return _error(503, problem)

    try:
        content = job()
    except EngineInputError as exc:
        return _error(400, str(exc))
    except EngineNotReady as exc:
        return _error(503, str(exc))
    except Exception as exc:  # noqa: BLE001 - reported to the UI
        SLOT.unload()  # a failed model may hold half its memory
        if "out of memory" in str(exc).lower():
            logger.exception("%s ran out of memory", engine_id)
            return _error(507, f"{engine.label} ran out of GPU/system memory. Close other GPU apps "
                               "(games, browsers with video), check the page file (LOCAL_SETUP.md, step 2) "
                               "or pick a lighter model.")
        logger.exception("%s failed", engine_id)
        return _error(500, f"{engine.label} failed: {exc}")
    return Response(content=content, media_type=media_type)
