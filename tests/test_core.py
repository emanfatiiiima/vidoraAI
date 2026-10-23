"""Unit tests for the framework-independent ``core`` package."""

from __future__ import annotations

import asyncio

import pytest

from core.exceptions import (
    AllProvidersFailedError,
    InvalidAIResponseError,
    ProviderFailedError,
    ProviderNotConfiguredError,
)
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


def test_parse_ai_string_list_accepts_local_model_shapes() -> None:
    assert parse_ai_string_list('{"topics": ["a", "b"], "count": 2}') == ["a", "b"]
    # Real Mistral 7B answer shape in Ollama's JSON mode.
    assert parse_ai_string_list('{"0": "\\"Mars: a\\"", "1": "b"}') == ["Mars: a", "b"]
    assert parse_ai_string_list('{"ideas": [{"title": "a", "id": 1}, {"title": "b"}]}') == ["a", "b"]


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


def test_router_uses_only_the_selected_provider() -> None:
    first = FakeProvider("first", ["from first"])
    second = FakeProvider("second", ["from second"])
    result = asyncio.run(LLMRouter([first, second]).generate("hi", provider="second"))
    assert (result.text, result.provider) == ("from second", "second")
    assert first.requests == []


def test_router_does_not_fall_back_from_selected_provider() -> None:
    first = FakeProvider("first", ["hello"])
    second = FakeProvider("second", [RuntimeError("quota")])
    with pytest.raises(ProviderFailedError) as info:
        asyncio.run(LLMRouter([first, second]).generate("hi", provider="second"))
    assert info.value.details["provider"] == "second"
    assert first.requests == []


def test_router_rejects_unconfigured_selected_provider() -> None:
    with pytest.raises(ProviderNotConfiguredError):
        asyncio.run(LLMRouter([FakeProvider("a")]).generate("hi", provider="b"))


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


# ---------------------------------------------------------------------- #
# Leonardo image provider
# ---------------------------------------------------------------------- #
def test_leonardo_client_polls_until_complete() -> None:
    import httpx

    from core.images import LeonardoClient

    polls = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer key"
        if request.method == "POST":
            return httpx.Response(200, json={"sdGenerationJob": {"generationId": "gen-1"}})
        polls.append(request)
        if len(polls) < 2:
            return httpx.Response(200, json={"generations_by_pk": {"status": "PENDING"}})
        images = [{"url": "https://cdn.leonardo.ai/img.jpg"}]
        return httpx.Response(200, json={"generations_by_pk": {"status": "COMPLETE", "generated_images": images}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = LeonardoClient(http=http, api_key="key", model_id="m", poll_interval_seconds=0)
            return await client.generate("a fox")

    assert asyncio.run(run()) == "https://cdn.leonardo.ai/img.jpg"
    assert len(polls) == 2


def test_leonardo_client_keeps_upstream_status() -> None:
    import httpx

    from core.exceptions import ExternalServiceError
    from core.images import LeonardoClient

    async def run():
        transport = httpx.MockTransport(lambda r: httpx.Response(429, json={"error": "quota"}))
        async with httpx.AsyncClient(transport=transport) as http:
            await LeonardoClient(http=http, api_key="key", model_id="m").generate("a fox")

    with pytest.raises(ExternalServiceError) as info:
        asyncio.run(run())
    assert info.value.upstream_status == 429


def test_image_service_raises_when_leonardo_not_configured() -> None:
    import httpx

    from core.services import ImageService

    async def run():
        async with httpx.AsyncClient() as http:
            service = ImageService(http=http, gemini=None, gemini_model="", openai=None, openai_model="")
            await service.generate("a fox", provider="leonardo")

    with pytest.raises(ProviderNotConfiguredError):
        asyncio.run(run())


def test_ai_options_verify_detects_invalid_key() -> None:
    import httpx

    from core.services import AIOptionsService

    async def run():
        transport = httpx.MockTransport(lambda r: httpx.Response(401))
        async with httpx.AsyncClient(transport=transport) as http:
            return await AIOptionsService(http, {"groq": "bad"}).verify("groq")

    status = asyncio.run(run())
    assert status.available is False
    assert "invalid" in status.reason


# ---------------------------------------------------------------------- #
# Local AI
# ---------------------------------------------------------------------- #
def test_ollama_provider_sends_json_mode_and_strips_thinking() -> None:
    import json

    import httpx

    from core.llm import LLMRequest
    from core.local import OllamaClient
    from core.local.ollama import OllamaProvider

    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": '<think>hmm</think> ["a"]'}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            provider = OllamaProvider(OllamaClient(http, "http://o", num_ctx=4096), "qwen3:8b")
            return provider.name, await provider.generate(LLMRequest("hi", json_mode=True))

    name, text = asyncio.run(run())
    assert name == "ollama:qwen3:8b"
    assert text == '["a"]'
    assert sent["format"] == "json" and sent["model"] == "qwen3:8b"
    assert sent["options"]["num_ctx"] == 4096 and sent["stream"] is False


def test_ai_options_lists_installed_ollama_models() -> None:
    import httpx

    from core.local import OllamaClient
    from core.services import AIOptionsService

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}, {"name": "gemma3:4b"}]})
        return httpx.Response(404)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            service = AIOptionsService(http, {}, ollama=OllamaClient(http, "http://o"), local_only=True)
            return await service.list_tasks(), await service.verify("ollama:llama3.1:8b")

    tasks, missing = asyncio.run(run())
    topics = next(t for t in tasks if t.id == "topics")
    # local_only hides the cloud AIs.
    assert [o.id for o in topics.options] == ["ollama:gemma3:4b", "ollama:qwen3:8b"]
    assert all(o.available and o.local for o in topics.options)
    assert missing.available is False and "ollama pull llama3.1:8b" in missing.reason


def test_scene_durations_follow_word_counts() -> None:
    from core.local.compile import MIN_SCENE_SECONDS, scene_durations

    assert scene_durations(30.0, [10, 20, 30]) == pytest.approx([5.0, 10.0, 15.0])
    # A one-word scene still gets the minimum, and the total is preserved.
    short = scene_durations(20.0, [1, 100])
    assert short[0] == pytest.approx(MIN_SCENE_SECONDS)
    assert sum(short) == pytest.approx(20.0)
    assert scene_durations(None, [5, 5]) == [5.0, 5.0]


def test_media_store_round_trip_and_path_safety(tmp_path) -> None:
    import httpx

    from core.local import MediaStore

    async def run():
        async with httpx.AsyncClient() as http:
            media = MediaStore(tmp_path, http)
            url = media.save(b"RIFF", "audio", ".wav")
            return media, url, await media.read(url)

    media, url, (content, content_type) = asyncio.run(run())
    assert url.startswith("/api/media/audio/") and url.endswith(".wav")
    assert (content, content_type) == (b"RIFF", "audio/wav")
    assert media.path_for("/api/media/../../etc/passwd") is None


def test_kdenlive_project_xml(tmp_path) -> None:
    from core.local import FFmpegCompiler, KdenliveCompiler, RenderSpec

    compiler = KdenliveCompiler(FFmpegCompiler("ffmpeg", RenderSpec(1080, 1920, 30)), melt_path=None)
    xml = compiler._project_xml([tmp_path / "a.mp4", tmp_path / "b.mp4"], [2.0, 1.0], tmp_path / "voice.wav")
    assert 'out="59"' in xml and 'out="29"' in xml
    assert 'mlt_service="mix"' in xml and "voice.wav" in xml


def test_local_engines_cover_every_requested_model() -> None:
    from local_ai.catalog import COMPILERS, engine_ids

    assert set(engine_ids("tts")) == {"kokoro", "piper", "xtts", "melo", "bark"}
    assert set(engine_ids("image")) == {"sd15", "sdxl-turbo", "sdxl", "flux-schnell"}
    assert set(engine_ids("video")) == {"svd-xt", "cogvideox-2b", "ltx-video", "wan-1.3b"}
    assert set(COMPILERS) == {"ffmpeg", "moviepy", "kdenlive"}
