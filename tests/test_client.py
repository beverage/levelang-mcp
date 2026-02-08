"""Tests for the Levelang HTTP client."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from sample_data import (
    SAMPLE_LANGUAGES_RESPONSE,
    SAMPLE_SINGLE_LANGUAGE,
    SAMPLE_TRANSLATION_RESPONSE,
)

from levelang_mcp.client import LevelangClient


BASE_URL = "http://testserver/api/v1"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Create a LevelangClient with no API key (isolated from .env)."""
    monkeypatch.delenv("LEVELANG_API_KEY", raising=False)
    from levelang_mcp.config import reset_settings

    reset_settings()

    c = LevelangClient()
    yield c

    reset_settings()


class TestTranslate:
    @respx.mock
    async def test_translate_success(self, client: LevelangClient):
        respx.post(f"{BASE_URL}/translate").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRANSLATION_RESPONSE)
        )
        result = await client.translate(
            text="Hello world",
            source_language_code="eng",
            target_language_code="fra",
            level="beginner",
            mood="casual",
        )
        assert result["translation"] == "Bonjour le monde"
        assert result["metadata"]["level"] == "A2"

    @respx.mock
    async def test_translate_sends_correct_body(self, client: LevelangClient):
        route = respx.post(f"{BASE_URL}/translate").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRANSLATION_RESPONSE)
        )
        await client.translate(
            text="Test",
            source_language_code="eng",
            target_language_code="deu",
            level="advanced",
            mood="formal",
        )
        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["text"] == "Test"
        assert body["source_language_code"] == "eng"
        assert body["target_language_code"] == "deu"
        assert body["level"] == "advanced"
        assert body["mood"] == "formal"

    @respx.mock
    async def test_translate_422_raises(self, client: LevelangClient):
        respx.post(f"{BASE_URL}/translate").mock(
            return_value=httpx.Response(422, json={"detail": "Invalid language code"})
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.translate("Hi", "eng", "xxx", "beginner", "casual")
        assert exc_info.value.response.status_code == 422

    @respx.mock
    async def test_translate_500_raises(self, client: LevelangClient):
        respx.post(f"{BASE_URL}/translate").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.translate("Hi", "eng", "fra", "beginner", "casual")


class TestGetLanguages:
    @respx.mock
    async def test_get_languages_success(self, client: LevelangClient):
        respx.get(f"{BASE_URL}/languages/details").mock(
            return_value=httpx.Response(200, json=SAMPLE_LANGUAGES_RESPONSE)
        )
        result = await client.get_languages()
        assert len(result["languages"]) == 2
        assert result["languages"][0]["code"] == "fra"

    @respx.mock
    async def test_get_languages_error(self, client: LevelangClient):
        respx.get(f"{BASE_URL}/languages/details").mock(
            return_value=httpx.Response(503, text="Service Unavailable")
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_languages()


class TestGetLanguage:
    @respx.mock
    async def test_get_language_success(self, client: LevelangClient):
        respx.get(f"{BASE_URL}/languages/fra").mock(
            return_value=httpx.Response(200, json=SAMPLE_SINGLE_LANGUAGE)
        )
        result = await client.get_language("fra")
        assert result["code"] == "fra"
        assert result["name"] == "French"

    @respx.mock
    async def test_get_language_not_found(self, client: LevelangClient):
        respx.get(f"{BASE_URL}/languages/xxx").mock(
            return_value=httpx.Response(404, json={"detail": "Language not found"})
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_language("xxx")
        assert exc_info.value.response.status_code == 404


class TestAuthHeaders:
    @respx.mock
    async def test_no_auth_header_when_no_key(self, client: LevelangClient):
        route = respx.get(f"{BASE_URL}/languages/details").mock(
            return_value=httpx.Response(200, json=SAMPLE_LANGUAGES_RESPONSE)
        )
        await client.get_languages()
        request = route.calls[0].request
        assert "Authorization" not in request.headers

    @respx.mock
    async def test_auth_header_when_key_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LEVELANG_API_KEY", "sk_test_key_123")
        from levelang_mcp.config import reset_settings

        reset_settings()

        authed_client = LevelangClient()
        route = respx.get(f"{BASE_URL}/languages/details").mock(
            return_value=httpx.Response(200, json=SAMPLE_LANGUAGES_RESPONSE)
        )
        await authed_client.get_languages()
        request = route.calls[0].request
        assert request.headers["Authorization"] == "Bearer sk_test_key_123"
