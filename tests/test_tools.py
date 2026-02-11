"""Tests for MCP tool implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx

from sample_data import SAMPLE_LANGUAGES_RESPONSE, SAMPLE_TRANSLATION_RESPONSE


class TestSanitizeText:
    def test_strips_leading_trailing_whitespace(self):
        from levelang_mcp.server import _sanitize_text

        assert _sanitize_text("  Hello world  ") == "Hello world"

    def test_preserves_internal_newlines(self):
        from levelang_mcp.server import _sanitize_text

        text = "Line one.\nLine two.\nLine three."
        assert _sanitize_text(text) == text

    def test_preserves_apostrophes(self):
        from levelang_mcp.server import _sanitize_text

        assert (
            _sanitize_text("I'm afraid I'll never understand")
            == "I'm afraid I'll never understand"
        )

    def test_preserves_unicode(self):
        from levelang_mcp.server import _sanitize_text

        assert _sanitize_text("Héllo wörld café") == "Héllo wörld café"

    def test_strips_surrounding_newlines(self):
        from levelang_mcp.server import _sanitize_text

        assert _sanitize_text("\n\n  Hello world  \n\n") == "Hello world"

    def test_empty_string(self):
        from levelang_mcp.server import _sanitize_text

        assert _sanitize_text("") == ""

    def test_whitespace_only(self):
        from levelang_mcp.server import _sanitize_text

        assert _sanitize_text("   \n\t  ") == ""


class TestTranslateTool:
    @patch("levelang_mcp.server.levelang")
    async def test_translate_returns_formatted_string(self, mock_client):
        mock_client.translate = AsyncMock(return_value=SAMPLE_TRANSLATION_RESPONSE)
        from levelang_mcp.server import translate

        result = await translate("Hello world", "fra", "beginner")
        assert "Translation: Bonjour le monde" in result
        assert "Level: A2" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_maps_field_names(self, mock_client):
        mock_client.translate = AsyncMock(return_value=SAMPLE_TRANSLATION_RESPONSE)
        from levelang_mcp.server import translate

        await translate(
            text="Hello",
            target_language="deu",
            level="advanced",
            source_language="eng",
            mood="formal",
        )
        mock_client.translate.assert_called_once_with(
            text="Hello",
            source_language_code="eng",
            target_language_code="deu",
            level="advanced",
            mood="formal",
        )

    @patch("levelang_mcp.server.levelang")
    async def test_translate_strips_whitespace_but_preserves_newlines(
        self, mock_client
    ):
        mock_client.translate = AsyncMock(return_value=SAMPLE_TRANSLATION_RESPONSE)
        from levelang_mcp.server import translate

        await translate(
            text="  Line one.\nLine two.  ",
            target_language="fra",
            level="beginner",
        )
        # Verify leading/trailing whitespace stripped but internal newlines preserved
        call_kwargs = mock_client.translate.call_args.kwargs
        assert call_kwargs["text"] == "Line one.\nLine two."

    @patch("levelang_mcp.server.levelang")
    async def test_translate_handles_422(self, mock_client):
        response = httpx.Response(
            422,
            json={"detail": "Invalid language code"},
            request=httpx.Request("POST", "http://test"),
        )
        mock_client.translate = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "", response=response, request=response.request
            )
        )
        from levelang_mcp.server import translate

        result = await translate("Hello", "xxx", "beginner")
        assert "Invalid request" in result
        assert "Invalid language code" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_handles_429(self, mock_client):
        response = httpx.Response(
            429, text="Too Many Requests", request=httpx.Request("POST", "http://test")
        )
        mock_client.translate = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "", response=response, request=response.request
            )
        )
        from levelang_mcp.server import translate

        result = await translate("Hello", "fra", "beginner")
        assert "Rate limit" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_handles_500(self, mock_client):
        response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("POST", "http://test"),
        )
        mock_client.translate = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "", response=response, request=response.request
            )
        )
        from levelang_mcp.server import translate

        result = await translate("Hello", "fra", "beginner")
        assert "temporarily unavailable" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_handles_timeout(self, mock_client):
        mock_client.translate = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        from levelang_mcp.server import translate

        result = await translate("Hello", "fra", "beginner")
        assert "timed out" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_handles_connection_error(self, mock_client):
        mock_client.translate = AsyncMock(side_effect=httpx.ConnectError("refused"))
        from levelang_mcp.server import translate

        result = await translate("Hello", "fra", "beginner")
        assert "Cannot reach" in result


class TestListLanguagesTool:
    @patch("levelang_mcp.server.levelang")
    async def test_list_languages_returns_formatted_string(self, mock_client):
        mock_client.get_languages = AsyncMock(return_value=SAMPLE_LANGUAGES_RESPONSE)
        from levelang_mcp.server import list_languages

        result = await list_languages()
        assert "French (fra)" in result
        assert "Mandarin Chinese (cmn)" in result

    @patch("levelang_mcp.server.levelang")
    async def test_list_languages_handles_connection_error(self, mock_client):
        mock_client.get_languages = AsyncMock(side_effect=httpx.ConnectError("refused"))
        from levelang_mcp.server import list_languages

        result = await list_languages()
        assert "Cannot reach" in result


class TestTranslateCompareTool:
    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_returns_all_levels(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [
                    {"code": "beginner", "display_name": "Beginner"},
                    {"code": "intermediate", "display_name": "Intermediate"},
                    {"code": "advanced", "display_name": "Advanced"},
                ],
                "moods": [{"code": "casual", "display_name": "Casual"}],
            }
        )
        mock_client.translate = AsyncMock(
            side_effect=[
                {
                    "translation": "Bonjour",
                    "transliteration": None,
                    "metadata": {"processing_time_ms": 800},
                },
                {
                    "translation": "Bonjour, comment allez-vous",
                    "transliteration": None,
                    "metadata": {"processing_time_ms": 900},
                },
                {
                    "translation": "Bonjour, comment vous portez-vous aujourd'hui",
                    "transliteration": None,
                    "metadata": {"processing_time_ms": 1000},
                },
            ]
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "Beginner" in result
        assert "Intermediate" in result
        assert "Advanced" in result
        assert "Bonjour" in result
        assert mock_client.translate.call_count == 3

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_unknown_language(self, mock_client):
        mock_client.get_language = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=httpx.Request("GET", "http://test/languages/xxx"),
                response=httpx.Response(404),
            )
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "xxx")
        assert "not found" in result.lower()

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_partial_failure(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [
                    {"code": "beginner", "display_name": "Beginner"},
                    {"code": "advanced", "display_name": "Advanced"},
                ],
                "moods": [],
            }
        )
        mock_client.translate = AsyncMock(
            side_effect=[
                {"translation": "Bonjour", "transliteration": None, "metadata": {}},
                Exception("Provider timeout"),
            ]
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "Beginner" in result
        assert "Bonjour" in result
        assert "Advanced" in result
        assert "Error" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_connection_error(self, mock_client):
        mock_client.get_language = AsyncMock(side_effect=httpx.ConnectError("refused"))
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "Cannot reach" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_timeout(self, mock_client):
        mock_client.get_language = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "timed out" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_generic_http_error(self, mock_client):
        mock_client.get_language = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=httpx.Request("GET", "http://test/languages/fra"),
                response=httpx.Response(500, text="Internal Server Error"),
            )
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "Backend error (HTTP 500)" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_empty_levels(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [],
                "moods": [],
            }
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra")
        assert "No proficiency levels" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_sanitizes_input(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [{"code": "beginner", "display_name": "Beginner"}],
                "moods": [],
            }
        )
        mock_client.translate = AsyncMock(
            return_value={
                "translation": "Bonjour",
                "transliteration": None,
                "metadata": {},
            }
        )
        from levelang_mcp.server import translate_compare

        await translate_compare("  Hello  ", "fra")
        call_kwargs = mock_client.translate.call_args.kwargs
        assert call_kwargs["text"] == "Hello"

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_subset_of_levels(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [
                    {"code": "beginner", "display_name": "Beginner"},
                    {"code": "intermediate", "display_name": "Intermediate"},
                    {"code": "advanced", "display_name": "Advanced"},
                    {"code": "fluent", "display_name": "Fluent"},
                ],
                "moods": [{"code": "casual", "display_name": "Casual"}],
            }
        )
        mock_client.translate = AsyncMock(
            side_effect=[
                {
                    "translation": "Bonjour",
                    "transliteration": None,
                    "metadata": {"processing_time_ms": 800},
                },
                {
                    "translation": "Bonjour, comment vous portez-vous aujourd'hui",
                    "transliteration": None,
                    "metadata": {"processing_time_ms": 1000},
                },
            ]
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare(
            "Hello", "fra", levels=["beginner", "advanced"]
        )
        assert "Beginner" in result
        assert "Advanced" in result
        assert "Intermediate" not in result
        assert "Fluent" not in result
        assert mock_client.translate.call_count == 2

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_invalid_levels(self, mock_client):
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [
                    {"code": "beginner", "display_name": "Beginner"},
                    {"code": "intermediate", "display_name": "Intermediate"},
                    {"code": "advanced", "display_name": "Advanced"},
                ],
                "moods": [],
            }
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra", levels=["beginner", "HSK1"])
        assert "Invalid level(s): HSK1" in result
        assert "beginner" in result
        assert "intermediate" in result
        assert "advanced" in result

    @patch("levelang_mcp.server.levelang")
    async def test_translate_compare_none_levels_compares_all(self, mock_client):
        """Passing levels=None (the default) should compare all available levels."""
        mock_client.get_language = AsyncMock(
            return_value={
                "name": "French",
                "code": "fra",
                "levels": [
                    {"code": "beginner", "display_name": "Beginner"},
                    {"code": "advanced", "display_name": "Advanced"},
                ],
                "moods": [],
            }
        )
        mock_client.translate = AsyncMock(
            side_effect=[
                {"translation": "Bonjour", "transliteration": None, "metadata": {}},
                {
                    "translation": "Bonjour, comment allez-vous",
                    "transliteration": None,
                    "metadata": {},
                },
            ]
        )
        from levelang_mcp.server import translate_compare

        result = await translate_compare("Hello", "fra", levels=None)
        assert "Beginner" in result
        assert "Advanced" in result
        assert mock_client.translate.call_count == 2
