"""AI selection endpoints - feed the "choose your AIs" popup shown before Step 1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import AIOptionsResponse, ProviderStatusResponse, VerifyProviderRequest

router = APIRouter(prefix="/ai-options", tags=["ai-options"])


@router.get("", response_model=AIOptionsResponse)
async def list_ai_options(services: ServicesDep) -> AIOptionsResponse:
    """Every task with its AI providers (cloud and local) and whether they can be used."""
    tasks = await services.ai_options.list_tasks()
    return AIOptionsResponse.model_validate({"tasks": [asdict(t) for t in tasks]})


@router.post("/verify", response_model=ProviderStatusResponse)
async def verify_ai_provider(body: VerifyProviderRequest, services: ServicesDep) -> ProviderStatusResponse:
    """Check that a provider works (API key accepted, or local model running and downloaded)."""
    status = await services.ai_options.verify(body.provider)
    return ProviderStatusResponse.model_validate(asdict(status))
