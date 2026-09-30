"""Step 2 - topic discovery and market research endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from core.services.topics import DEFAULT_AUDIENCE
from fastapi_backend.dependencies import ServicesDep
from fastapi_backend.schemas import (
    BasicTopicsRequest,
    NewsResponse,
    NicheRequest,
    TopicsResponse,
)

router = APIRouter(tags=["topics"])


@router.post("/topics/basic", response_model=TopicsResponse)
async def basic_topics(body: BasicTopicsRequest, services: ServicesDep) -> TopicsResponse:
    """10 evergreen topic ideas for the niche."""
    topics = await services.topics.generate_basic(
        body.niche, body.duration, body.audience or DEFAULT_AUDIENCE, body.provider
    )
    return TopicsResponse(topics=topics)


@router.post("/topics/unique", response_model=TopicsResponse)
async def unique_topics(body: NicheRequest, services: ServicesDep) -> TopicsResponse:
    """10 creative, viral-style topic ideas."""
    return TopicsResponse(topics=await services.topics.generate_unique(body.niche, body.provider))


@router.post("/topics/trending", response_model=TopicsResponse)
async def trending_topics(body: NicheRequest, services: ServicesDep) -> TopicsResponse:
    """10 topic ideas grounded in live news headlines and Google Trends."""
    return TopicsResponse(topics=await services.topics.generate_trending(body.niche, body.provider))


@router.get("/trends")
async def trends(services: ServicesDep, q: str | None = Query(default=None)) -> dict[str, Any]:
    """Raw Google Trends data from SerpApi (simulated when no key is set)."""
    return await services.research.get_trends(q)


@router.get("/news", response_model=NewsResponse)
async def news(services: ServicesDep, q: str = Query(default="")) -> NewsResponse:
    """Latest Google News headlines for a query (empty list on failure)."""
    return NewsResponse(headlines=await services.research.get_news_headlines(q))
