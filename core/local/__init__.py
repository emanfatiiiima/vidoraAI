"""
Local AI integration for the backend.

| Module    | What it does                                                    |
|-----------|-----------------------------------------------------------------|
| ollama    | Text generation with any model pulled into Ollama               |
| worker    | HTTP client for the GPU worker (``python -m local_ai``)         |
| media     | Stores generated audio/clips/videos, served at ``/api/media``   |
| compile   | Final render with FFmpeg, MoviePy or Kdenlive (MLT)             |

Model lists and labels come from :mod:`local_ai.catalog`, shared with the worker.
"""

from core.local.compile import (
    CompileError,
    CompileJob,
    FFmpegCompiler,
    KdenliveCompiler,
    MoviePyCompiler,
    RenderSpec,
)
from core.local.media import MediaStore
from core.local.ollama import OllamaClient, OllamaError, provider_resolver
from core.local.worker import LocalWorkerClient

__all__ = [
    "CompileError",
    "CompileJob",
    "FFmpegCompiler",
    "KdenliveCompiler",
    "LocalWorkerClient",
    "MediaStore",
    "MoviePyCompiler",
    "OllamaClient",
    "OllamaError",
    "RenderSpec",
    "provider_resolver",
]
