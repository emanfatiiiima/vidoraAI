"""Generic text generation endpoint (raw prompt in, text out)."""

from __future__ import annotations

from fastapi import APIRouter

from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import GenerateRequest, GenerateResponse

router = APIRouter(tags=["generation"])

JSON_MIME_TYPE = "application/json"


@router.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest, services: ServicesDep) -> GenerateResponse:
    """Run a raw prompt through the LLM fallback chain (Gemini -> OpenAI -> Groq)."""
    result = await services.llm.generate(
        body.prompt,
        system_prompt=body.system_prompt,
        json_mode=body.response_mime_type == JSON_MIME_TYPE,
    )
    return GenerateResponse(text=result.text, provider=result.provider)
