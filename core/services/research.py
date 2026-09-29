"""
Market research: Google Trends (via SerpApi) and Google News headlines.

This data is used as real-time context when generating "trending" topics.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/search"

# Very lightweight headline extraction from the Google News HTML page.
# NOTE: this depends on Google's markup and may break if they change it;
# a proper news API is recommended for production use.
_HEADLINE_RE = re.compile(r'<a[^>]*class="WwrUic"[^>]*>([^<]+)</a>')
MAX_HEADLINES = 5


class ResearchService:
    """Fetches trend and news data for a niche."""

    def __init__(self, http: httpx.AsyncClient, serpapi_key: str | None) -> None:
        self._http = http
        self._serpapi_key = serpapi_key

    async def get_trends(self, query: str | None) -> dict[str, Any]:
        """Return Google Trends data for ``query``.

        Without a SerpApi key, returns a small simulated ``trending_searches``
        payload so the rest of the pipeline keeps working in development.

        Raises:
            ExternalServiceError: SerpApi call failed.
        """
        if not self._serpapi_key:
            return {
                "trending_searches": [
                    {"query": f"{query} innovations 2026"},
                    {"query": f"future of {query}"},
                    {"query": f"new {query} techniques"},
                ]
            }

        try:
            response = await self._http.get(
                SERPAPI_URL,
                params={
                    "engine": "google_trends",
                    "q": query or "technology",
                    "api_key": self._serpapi_key,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"SerpApi request failed: {exc}") from exc

    async def get_news_headlines(self, query: str) -> list[str]:
        """Return up to 5 recent Google News headlines for ``query``.

        Never raises: on any failure an empty list is returned, because news is
        optional "nice to have" context.
        """
        try:
            response = await self._http.get(
                GOOGLE_NEWS_SEARCH_URL,
                params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("News scraping failed: %s", exc)
            return []

        return [h.strip() for h in _HEADLINE_RE.findall(response.text)[:MAX_HEADLINES]]

    async def build_trend_context(self, niche: str) -> str:
        """Combine news headlines and trending searches into a single prompt context.

        Each source is optional; failures are logged and skipped.
        """
        context = ""

        headlines = await self.get_news_headlines(niche)
        if headlines:
            context += f"Current News Headlines for {niche}: {' | '.join(headlines)}. "

        try:
            trends = await self.get_trends(niche)
            searches = trends.get("trending_searches") or []
            queries = [t.get("query") for t in searches if isinstance(t, dict) and t.get("query")]
            if queries:
                context += f"Top Trending Searches: {', '.join(queries)}."
        except ExternalServiceError as exc:
            logger.warning("Trends API failed: %s", exc)

        return context
