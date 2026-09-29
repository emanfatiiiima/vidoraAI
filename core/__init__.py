"""
VidoraAI core package.

This package contains ALL business logic of the application and is completely
independent of any web framework. The FastAPI backend (``fastapi_backend``) is a
thin HTTP layer on top of it, which means the same functionality can also be
used from scripts, CLI tools, background workers or tests.

Layout
------
- ``config``      : typed application settings loaded from environment / ``.env``
- ``exceptions``  : domain errors raised by the core (mapped to HTTP by the backend)
- ``prompts``     : every LLM prompt template used by the app
- ``llm``         : text-generation providers (Gemini, OpenAI, Groq) + fallback router
- ``services``    : one module per feature (topics, scripts, scenes, audio, ...)
- ``utils``       : small, pure helper functions
- ``container``   : wires settings + providers + services together
"""

from core.config import Settings, get_settings
from core.container import Services, build_services

__all__ = ["Settings", "get_settings", "Services", "build_services"]
