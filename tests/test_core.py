"""Unit tests for the framework-independent ``core`` package."""

from __future__ import annotations

import asyncio

import pytest

from core.exceptions import AllProvidersFailedError, InvalidAIResponseError
from core.llm import LLMRouter
from core.services.export import ExportFormat, export_script
from core.services.scenes import split_script_evenly
from core.utils import parse_ai_json, parse_ai_string_list
from tests.conftest import FakeProvider


# ---------------------------------------------------------------------- #
# JSON parsing
# ---------------------------------------------------------------------- #
def test_parse_ai_json_strips_code_fences() -> None:
    assert parse_ai_json('```json\n["a", "b"]\n```') == ["a", "b"]


def test_parse_ai_json_unwraps_single_key_object() -> None:
    assert parse_ai_json('{"topics": ["a", "b"]}') == ["a", "b"]


def test_parse_ai_json_returns_none_for_invalid_json() -> None:
    assert parse_ai_json("not json") is None


def test_parse_ai_string_list_drops_non_strings() -> None:
    assert parse_ai_string_list('["a", 1, " b ", ""]') == ["a", "b"]
    assert parse_ai_string_list('{"a": 1, "b": 2}') is None


# ---------------------------------------------------------------------- #
# LLM router
# ---------------------------------------------------------------------- #
def test_router_falls_back_to_next_provider() -> None:
    first = FakeProvider("first", [RuntimeError("quota")])
    second = FakeProvider("second", ["hello"])
    result = asyncio.run(LLMRouter([first, second]).generate("hi"))
    assert (result.text, result.provider) == ("hello", "second")


def test_router_raises_when_all_providers_fail() -> None:
    router = LLMRouter([FakeProvider("a", [RuntimeError("x")])])
    with pytest.raises(AllProvidersFailedError):
        asyncio.run(router.generate("hi"))


def test_router_raises_when_no_provider_configured() -> None:
    with pytest.raises(AllProvidersFailedError):
        asyncio.run(LLMRouter([]).generate("hi"))


# ---------------------------------------------------------------------- #
# Services
# ---------------------------------------------------------------------- #
def test_basic_topics_are_capped_at_ten(services, fake_llm) -> None:
    fake_llm.answers = [str([f"topic {i}" for i in range(15)]).replace("'", '"')]
    topics = asyncio.run(services.topics.generate_basic("AI", "10 minutes"))
    assert len(topics) == 10
    assert fake_llm.requests[0].json_mode is True


def test_topics_raise_on_invalid_ai_output(services, fake_llm) -> None:
    fake_llm.answers = ["sorry, I can't do that"]
    with pytest.raises(InvalidAIResponseError):
        asyncio.run(services.topics.generate_unique("AI"))


def test_split_script_uses_ai_segments(services, fake_llm) -> None:
    fake_llm.answers = ['["one", "two", "three"]']
    assert asyncio.run(services.scenes.split_script("script", 2)) == ["one", "two"]


def test_split_script_falls_back_to_even_split(services, fake_llm) -> None:
    fake_llm.answers = ["not json"]
    script = "First sentence here. Second sentence here. Third sentence here. Fourth one here."
    scenes = asyncio.run(services.scenes.split_script(script, 2))
    assert scenes == [
        "First sentence here. Second sentence here",
        "Third sentence here. Fourth one here",
    ]


def test_split_script_evenly_returns_requested_count() -> None:
    assert len(split_script_evenly("Only one sentence here.", 3)) == 3


def test_export_txt_and_docx() -> None:
    txt = export_script("My Topic", "line 1\nline 2", ExportFormat.TXT)
    assert txt.decode() == "TOPIC: My Topic\n\nSCRIPT:\nline 1\nline 2"

    docx_bytes = export_script("My Topic", "line 1", ExportFormat.DOCX)
    assert docx_bytes[:2] == b"PK"  # .docx files are zip archives


# ---------------------------------------------------------------------- #
# Resilient downloads
# ---------------------------------------------------------------------- #
def test_fetch_bytes_retries_rate_limits() -> None:
    import httpx

    from core.utils import fetch_bytes

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) < 3:
            return httpx.Response(402)
        return httpx.Response(200, content=b"img", headers={"content-type": "image/jpeg"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await fetch_bytes(http, "https://example.com/x", backoff_seconds=0)

    assert asyncio.run(run()) == (b"img", "image/jpeg")
    assert len(calls) == 3


def test_image_service_returns_data_uri_from_pollinations() -> None:
    import httpx

    from core.services import ImageService

    transport = httpx.MockTransport(
        lambda r: httpx.Response(200, content=b"jpg", headers={"content-type": "image/jpeg"})
    )

    async def run():
        async with httpx.AsyncClient(transport=transport) as http:
            service = ImageService(http=http, gemini=None, gemini_model="", openai=None, openai_model="")
            return await service.generate("a fox")

    assert asyncio.run(run()) == "data:image/jpeg;base64,anBn"
