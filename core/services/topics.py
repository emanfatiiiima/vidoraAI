"""
Topic discovery (Step 2 of the video pipeline).

Three flavours of topic ideas are offered:

- **basic**    : evergreen ideas for the niche
- **unique**   : more creative, "hooky" ideas
- **trending** : ideas grounded in live news + Google Trends data
"""

from __future__ import annotations

from core import prompts
from core.exceptions import InvalidAIResponseError
from core.llm import LLMRouter
from core.services.research import ResearchService
from core.utils import parse_ai_string_list

#: Maximum number of topics returned per category.
MAX_TOPICS = 10
DEFAULT_AUDIENCE = "YouTube Viewers"
UNIQUE_TOPIC_CONTEXT = "high impact viral concepts"
TRENDING_FALLBACK_CONTEXT = "emerging patterns in the niche"


class TopicService:
    """Generates topic ideas for a niche."""

    def __init__(self, llm: LLMRouter, research: ResearchService) -> None:
        self._llm = llm
        self._research = research

    async def generate_basic(
        self, niche: str, duration: str, audience: str = DEFAULT_AUDIENCE
    ) -> list[str]:
        """Evergreen topic ideas for ``niche``."""
        prompt = prompts.topic_generator_basic(niche, duration, audience)
        return await self._generate_topic_list(prompt)

    async def generate_unique(self, niche: str) -> list[str]:
        """Creative, viral-style topic ideas for ``niche``."""
        prompt = prompts.topic_generator_unique(niche, UNIQUE_TOPIC_CONTEXT)
        return await self._generate_topic_list(prompt)

    async def generate_trending(self, niche: str) -> list[str]:
        """Topic ideas based on live news headlines and trending searches."""
        context = await self._research.build_trend_context(niche)
        prompt = prompts.topic_generator_unique(
            niche, f"Real-time data detected: {context or TRENDING_FALLBACK_CONTEXT}"
        )
        return await self._generate_topic_list(prompt)

    async def _generate_topic_list(self, prompt: str) -> list[str]:
        """Ask the LLM for a JSON list of topics and validate the result.

        Raises:
            InvalidAIResponseError: the AI did not return a JSON array of strings.
        """
        response = await self._llm.generate(prompt, json_mode=True)
        topics = parse_ai_string_list(response.text)
        if topics is None:
            raise InvalidAIResponseError("AI returned invalid topic format.")
        return topics[:MAX_TOPICS]
