"""
Script writing (Step 3 of the video pipeline).

Generates the narrator's voice-over script for a topic and a short summary
of it ("narrative strategy").
"""

from __future__ import annotations

from core import prompts
from core.llm import LLMRouter


class ScriptService:
    """Generates and summarises video scripts.

    ``provider`` selects a single LLM provider (the user's choice, no fallback);
    ``None`` uses the router's automatic order.
    """

    def __init__(self, llm: LLMRouter) -> None:
        self._llm = llm

    async def generate_script(
        self, topic: str, niche: str, duration: str, style: str, provider: str | None = None
    ) -> str:
        """Write a TTS-ready voice-over script."""
        response = await self._llm.generate(
            prompts.script_generator(topic, niche, duration, style), provider=provider
        )
        return response.text

    async def summarize(self, script: str, provider: str | None = None) -> str:
        """Summarise ``script`` to roughly a quarter of its length."""
        response = await self._llm.generate(prompts.summary_generator(script), provider=provider)
        return response.text
