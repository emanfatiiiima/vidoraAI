"""
Shared runtime of the GPU worker: settings, the single "model slot" and
helpers that keep an 8 GB card from running out of memory.

Only ONE model is kept on the GPU at a time. Asking for a different engine
unloads the current one first, and Ollama is asked to release its VRAM before a
diffusion/TTS model is loaded. An idle model is unloaded after a while so
Ollama gets the whole GPU back for the text steps.
"""

from __future__ import annotations

import gc
import json
import logging
import os
import threading
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger("local_ai")

PACKAGE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------- #
# Settings (plain environment variables - this venv has no pydantic-settings)
# ---------------------------------------------------------------------- #
HOST = os.environ.get("LOCAL_AI_HOST", "127.0.0.1")
PORT = int(os.environ.get("LOCAL_AI_PORT", "8001"))
MODELS_DIR = Path(os.environ.get("LOCAL_AI_MODELS_DIR", PACKAGE_DIR / "models"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
#: Python of the separate MeloTTS venv.
MELO_PYTHON = Path(
    os.environ.get(
        "MELO_PYTHON",
        PACKAGE_DIR / ".venv-melo" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    )
)
#: Seconds a model may sit unused on the GPU before it is unloaded (0 = never).
IDLE_UNLOAD_SECONDS = float(os.environ.get("LOCAL_AI_IDLE_UNLOAD_SECONDS", "180"))

READY_DIR = MODELS_DIR / ".ready"


def mark_ready(engine_id: str) -> None:
    """Record that every file of ``engine_id`` was downloaded (see ``local_ai.download``)."""
    READY_DIR.mkdir(parents=True, exist_ok=True)
    (READY_DIR / engine_id).write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")


def is_ready(engine_id: str) -> bool:
    return (READY_DIR / engine_id).is_file()


# ---------------------------------------------------------------------- #
# Errors with a user-facing message
# ---------------------------------------------------------------------- #
class EngineNotReady(RuntimeError):
    """The engine can't run yet (package missing, model not downloaded, ...)."""


class EngineInputError(ValueError):
    """The request can't be processed (empty text, bad voice, ...)."""


# ---------------------------------------------------------------------- #
# GPU helpers
# ---------------------------------------------------------------------- #
def cuda_device() -> str:
    import torch

    if not torch.cuda.is_available():
        raise EngineNotReady(
            "PyTorch can't see a CUDA GPU. Reinstall torch with the CUDA build "
            "(see LOCAL_SETUP.md, step 4) and check `nvidia-smi`."
        )
    return "cuda"


def free_cuda() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except ImportError:
        pass


def free_ollama_vram() -> None:
    """Ask Ollama to unload every model it holds, so a diffusion model fits in VRAM."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/ps", timeout=3) as response:
            models = json.load(response).get("models") or []
    except Exception:  # noqa: BLE001 - Ollama not running = nothing to free
        return
    for model in models:
        name = model.get("name") or model.get("model")
        if not name:
            continue
        body = json.dumps({"model": name, "keep_alive": 0}).encode()
        request = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate", data=body, headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request, timeout=30).read()
            logger.info("Asked Ollama to unload %s to free VRAM.", name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not unload Ollama model %s: %s", name, exc)


def gpu_info() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {"cuda": False, "reason": "torch is not installed"}
    if not torch.cuda.is_available():
        return {"cuda": False, "torch": torch.__version__}
    free, total = torch.cuda.mem_get_info()
    return {
        "cuda": True,
        "torch": torch.__version__,
        "name": torch.cuda.get_device_name(0),
        "vram_total_gb": round(total / 1e9, 1),
        "vram_free_gb": round(free / 1e9, 1),
    }


# ---------------------------------------------------------------------- #
# The model slot
# ---------------------------------------------------------------------- #
class ModelSlot:
    """Holds at most one loaded model and serialises every GPU job.

    Usage::

        with SLOT.use("sdxl", load_sdxl) as pipe:
            image = pipe(prompt).images[0]
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._engine: str | None = None
        self._model: Any = None
        self._last_used = time.monotonic()
        if IDLE_UNLOAD_SECONDS > 0:
            threading.Thread(target=self._idle_watch, daemon=True).start()

    @property
    def loaded(self) -> str | None:
        return self._engine

    def use(self, engine_id: str, loader: Callable[[], Any]) -> _SlotUse:
        return _SlotUse(self, engine_id, loader)

    def unload(self) -> None:
        with self._lock:
            if self._engine is not None:
                logger.info("Unloading %s from the GPU.", self._engine)
            self._engine = None
            self._model = None
            free_cuda()

    def _acquire(self, engine_id: str, loader: Callable[[], Any]) -> Any:
        self._lock.acquire()
        try:
            if self._engine != engine_id:
                self.unload()
                free_ollama_vram()
                logger.info("Loading %s (the first load after a download takes longer)...", engine_id)
                started = time.monotonic()
                self._model = loader()
                self._engine = engine_id
                logger.info("%s loaded in %.0fs.", engine_id, time.monotonic() - started)
            return self._model
        except BaseException:
            self.unload()
            self._lock.release()
            raise

    def _release(self) -> None:
        self._last_used = time.monotonic()
        free_cuda()  # drop activations of the finished job, keep the weights
        self._lock.release()

    def _idle_watch(self) -> None:
        while True:
            time.sleep(15)
            if self._engine is None or time.monotonic() - self._last_used < IDLE_UNLOAD_SECONDS:
                continue
            if self._lock.acquire(blocking=False):
                try:
                    if time.monotonic() - self._last_used >= IDLE_UNLOAD_SECONDS:
                        self.unload()
                finally:
                    self._lock.release()


class _SlotUse:
    def __init__(self, slot: ModelSlot, engine_id: str, loader: Callable[[], Any]) -> None:
        self._slot, self._engine_id, self._loader = slot, engine_id, loader

    def __enter__(self) -> Any:
        return self._slot._acquire(self._engine_id, self._loader)

    def __exit__(self, *exc: object) -> None:
        self._slot._release()


SLOT = ModelSlot()
