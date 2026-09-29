"""Health check endpoint (useful for Docker, load balancers and quick sanity checks)."""

from __future__ import annotations

from fastapi import APIRouter

from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(services: ServicesDep) -> HealthResponse:
    """Report that the API is up and which LLM providers are configured."""
    return HealthResponse(status="ok", llm_providers=services.llm.provider_names)
