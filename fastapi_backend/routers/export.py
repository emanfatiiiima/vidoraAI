"""Step 8 - download the whole project as a ZIP package."""

from __future__ import annotations

import re

from fastapi import APIRouter, Response

from core.services import ProjectData, ProjectScene
from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import ProjectExportRequest

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/project")
async def export_project(body: ProjectExportRequest, services: ServicesDep) -> Response:
    """ZIP with project details (Excel), script, images, clips, narration and final video."""
    project = ProjectData(
        niche=body.niche,
        style=body.style,
        duration=body.duration,
        aspect_ratio=body.aspect_ratio,
        scene_count=body.scene_count,
        topic=body.topic,
        script=body.script,
        summary=body.summary,
        audio_url=body.audio_url,
        final_video_url=body.final_video_url,
        scenes=[
            ProjectScene(text=s.text, prompt=s.prompt, image_url=s.selected_image, video_url=s.video_url)
            for s in body.scenes
        ],
    )
    content = await services.project_export.build_zip(project)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{_zip_name(body.topic)}"'},
    )


def _zip_name(topic: str) -> str:
    """ASCII-safe file name derived from the topic, e.g. ``The_AI_Revolution.zip``."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", topic).strip("_")[:50]
    return f"{slug or 'vidora_project'}.zip"
