"""
Shared test fixtures.

Tests never call real AI providers: :class:`FakeProvider` returns canned
answers so the logic in ``core`` and the HTTP layer can be tested offline.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from core import Services
from core.config import Settings
from core.llm import LLMProvider, LLMRequest, LLMRouter
from core.services import (
    ImageService,
    ResearchService,
    SceneService,
    ScriptService,
    TextToSpeechService,
    TopicService,
    VideoService,
)
from fastapi_backend.dependencies import get_services
from fastapi_backend.main import create_app


class FakeProvider(LLMProvider):
    """LLM provider that returns queued answers (or raises queued exceptions)."""

    def __init__(self, name: str = "fake", answers: list[str | Exception] | None = None) -> None:
        self.name = name
        self.answers = list(answers or [])
        self.requests: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> str:
        self.requests.append(request)
        answer = self.answers.pop(0) if self.answers else "default answer"
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture
def fake_llm() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def services(fake_llm: FakeProvider) -> Services:
    """A Services bundle wired to the fake LLM and with no external API keys."""
    llm = LLMRouter([fake_llm])
    http = httpx.AsyncClient()
    research = ResearchService(http, serpapi_key=None)
    return Services(
        llm=llm,
        research=research,
        topics=TopicService(llm, research),
        scripts=ScriptService(llm),
        scenes=SceneService(llm),
        tts=TextToSpeechService(http, api_key=None),
        images=ImageService(gemini=None, gemini_model="", openai=None, openai_model=""),
        video=VideoService(clip_delay_seconds=0, compile_delay_seconds=0),
    )


@pytest.fixture
def client(services: Services, tmp_path) -> Iterator[TestClient]:
    """HTTP test client using the fake services (no lifespan, no real keys)."""
    app = create_app(Settings(_env_file=None, frontend_dist_dir=tmp_path / "missing"))
    app.dependency_overrides[get_services] = lambda: services
    yield TestClient(app)
