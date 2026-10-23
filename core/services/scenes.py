"""
Scene planning (Step 5 of the video pipeline).

Splits the script into scenes and writes a detailed image prompt per scene.
"""

from __future__ import annotations

import math
import re

from core import prompts
from core.llm import LLMRouter
from core.utils import parse_ai_string_list

# Sentences shorter than this are ignored by the fallback splitter.
_MIN_SENTENCE_LENGTH = 5
_SENTENCE_END_RE = re.compile(r"[.!?]+")
PROMPT_FAILED_PLACEHOLDER = "Failed to generate prompt"


def split_script_evenly(script: str, scene_count: int) -> list[str]:
    """Deterministic fallback: split ``script`` into ``scene_count`` chunks of sentences.

    Used when the AI does not return a valid JSON list of scenes.
    """
    sentences = [
        s.strip()
        for s in _SENTENCE_END_RE.split(script)
        if len(s.strip()) > _MIN_SENTENCE_LENGTH
    ]
    size = math.ceil(len(sentences) / scene_count)
    return [". ".join(sentences[i * size : (i + 1) * size]) for i in range(scene_count)]


class SceneService:
    """Breaks a script into scenes and designs visuals for each one.

    Scene work is text generation, so the UI sends the user's *script* AI as
    ``provider`` (no fallback); ``None`` uses the router's automatic order.
    """

    def __init__(self, llm: LLMRouter) -> None:
        self._llm = llm

    async def split_script(self, script: str, scene_count: int, provider: str | None = None) -> list[str]:
        """Split ``script`` into at most ``scene_count`` scene texts.

        The AI is asked for logical, story-aware segments. If its answer can't
        be parsed, the script is split evenly by sentences instead.
        """
        response = await self._llm.generate(prompts.script_splitter(script, scene_count), provider=provider)
        chunks = parse_ai_string_list(response.text) or split_script_evenly(script, scene_count)
        return chunks[:scene_count]

    async def generate_scene_prompt(self, scene_text: str, style: str, provider: str | None = None) -> str:
        """Write a detailed Midjourney-style image prompt for one scene."""
        response = await self._llm.generate(
            prompts.scene_prompt_generator(scene_text, style), provider=provider
        )
        return response.text or PROMPT_FAILED_PLACEHOLDER
