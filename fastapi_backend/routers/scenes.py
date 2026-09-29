"""Step 5 - scene planning endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import (
    ScenePromptRequest,
    ScenePromptResponse,
    SplitScenesRequest,
    SplitScenesResponse,
)

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("/split", response_model=SplitScenesResponse)
async def split_scenes(body: SplitScenesRequest, services: ServicesDep) -> SplitScenesResponse:
    """Split the script into ``sceneCount`` scene texts."""
    scenes = await services.scenes.split_script(body.script, body.scene_count)
    return SplitScenesResponse(scenes=scenes)


@router.post("/prompt", response_model=ScenePromptResponse)
async def scene_prompt(body: ScenePromptRequest, services: ServicesDep) -> ScenePromptResponse:
    """Generate a detailed image prompt for one scene."""
    prompt = await services.scenes.generate_scene_prompt(body.text, body.style)
    return ScenePromptResponse(prompt=prompt)
