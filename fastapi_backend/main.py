"""
FastAPI application entry point.

Run in development (from the project root)::

    uvicorn fastapi_backend.main:app --reload --port 8000

The backend is intentionally thin: it validates HTTP input, calls a service
from ``core`` and returns the result. All business logic lives in ``core``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import Settings, build_services, get_settings
from fastapi_backend.errors import register_exception_handlers
from fastapi_backend.routers import api_router

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory - builds a fully configured FastAPI instance."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # One shared HTTP client for the whole process (connection pooling).
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        ) as http:
            app.state.services = build_services(settings, http)
            yield

    app = FastAPI(
        title="VidoraAI API",
        description="Backend for the VidoraAI video-production pipeline.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)

    # In production the built React app is served by FastAPI itself, so the
    # whole product runs as a single process on a single port.
    # Mounted last so it never shadows /api routes or the /docs pages.
    if settings.frontend_dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dist_dir, html=True), name="frontend")
        logger.info("Serving frontend from %s", settings.frontend_dist_dir)

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
app = create_app()
