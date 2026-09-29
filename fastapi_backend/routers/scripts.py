"""Step 3 - script writing, summary and export endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response

from core.services.export import MEDIA_TYPES, export_script
from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import (
    ExportRequest,
    ScriptRequest,
    ScriptResponse,
    SummaryRequest,
    SummaryResponse,
)

router = APIRouter(prefix="/script", tags=["script"])


@router.post("", response_model=ScriptResponse)
async def generate_script(body: ScriptRequest, services: ServicesDep) -> ScriptResponse:
    """Write a TTS-ready voice-over script for the selected topic."""
    script = await services.scripts.generate_script(
        body.topic, body.niche, body.duration, body.style
    )
    return ScriptResponse(script=script)


@router.post("/summary", response_model=SummaryResponse)
async def summarize_script(body: SummaryRequest, services: ServicesDep) -> SummaryResponse:
    """Short summary ("narrative strategy") of a script."""
    return SummaryResponse(summary=await services.scripts.summarize(body.script))


@router.post("/export")
async def export(body: ExportRequest) -> Response:
    """Download the script as a TXT or DOCX file."""
    content = export_script(body.topic, body.script, body.format)
    return Response(
        content=content,
        media_type=MEDIA_TYPES[body.format],
        headers={"Content-Disposition": f'attachment; filename="script.{body.format.value}"'},
    )
