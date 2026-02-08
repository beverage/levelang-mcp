"""Tests for response formatting functions."""

from __future__ import annotations

from sample_data import (
    SAMPLE_LANGUAGES_RESPONSE,
    SAMPLE_SINGLE_LANGUAGE,
    SAMPLE_TRANSLATION_RESPONSE,
    SAMPLE_TRANSLATION_WITH_TRANSLIT,
)

from levelang_mcp.formatting import (
    format_language_detail,
    format_language_list,
    format_translation,
)


class TestFormatTranslation:
    def test_basic_translation(self):
        result = format_translation(SAMPLE_TRANSLATION_RESPONSE)
        assert "Translation: Bonjour le monde" in result
        assert "Level: A2 (elementary proficiency)" in result
        assert "Mood: Casual" in result
        assert "Provider: gemini / gemini-2.5-flash-lite" in result
        assert "Processing time: 800ms" in result

    def test_transliteration_omitted_when_null(self):
        result = format_translation(SAMPLE_TRANSLATION_RESPONSE)
        assert "Transliteration" not in result

    def test_transliteration_included_when_present(self):
        result = format_translation(SAMPLE_TRANSLATION_WITH_TRANSLIT)
        assert "Transliteration: n\u01d0 h\u01ceo sh\u00ec ji\u00e8" in result

    def test_transcription_omitted_when_null(self):
        result = format_translation(SAMPLE_TRANSLATION_RESPONSE)
        assert "Transcription" not in result

    def test_transcription_included_when_present(self):
        response = {
            **SAMPLE_TRANSLATION_RESPONSE,
            "transcription": "Hello world",
        }
        result = format_translation(response)
        assert "Transcription: Hello world" in result

    def test_minimal_metadata(self):
        response = {
            "translation": "Bonjour",
            "transliteration": None,
            "transcription": None,
            "metadata": {},
        }
        result = format_translation(response)
        assert result == "Translation: Bonjour"


class TestFormatLanguageList:
    def test_formats_multiple_languages(self):
        result = format_language_list(SAMPLE_LANGUAGES_RESPONSE)
        assert "French (fra)" in result
        assert "Mandarin Chinese (cmn)" in result

    def test_shows_levels(self):
        result = format_language_list(SAMPLE_LANGUAGES_RESPONSE)
        assert "Beginner, Intermediate, Advanced, Fluent" in result

    def test_shows_moods(self):
        result = format_language_list(SAMPLE_LANGUAGES_RESPONSE)
        assert "Casual, Polite, Formal" in result

    def test_shows_transliteration(self):
        result = format_language_list(SAMPLE_LANGUAGES_RESPONSE)
        # French: No, Mandarin: Yes
        fra_section = result.split("Mandarin")[0]
        cmn_section = result.split("Mandarin")[1]
        assert "Transliteration: No" in fra_section
        assert "Transliteration: Yes" in cmn_section

    def test_empty_languages(self):
        result = format_language_list({"languages": [], "total_count": 0})
        assert result == "No languages available."


class TestFormatLanguageDetail:
    def test_header(self):
        result = format_language_detail(SAMPLE_SINGLE_LANGUAGE)
        assert result.startswith("French (fra)")

    def test_levels_with_descriptions(self):
        result = format_language_detail(SAMPLE_SINGLE_LANGUAGE)
        assert "Beginner: Basic vocabulary" in result
        assert "Intermediate: Complex structures" in result

    def test_moods_with_default_marker(self):
        result = format_language_detail(SAMPLE_SINGLE_LANGUAGE)
        assert "Casual (default): Everyday conversation" in result
        assert "Formal: Professional contexts" in result
        # Formal should NOT have default marker
        assert "Formal (default)" not in result

    def test_transliteration_shown(self):
        result = format_language_detail(SAMPLE_SINGLE_LANGUAGE)
        assert "Transliteration: No" in result

    def test_can_be_used_as(self):
        result = format_language_detail(SAMPLE_SINGLE_LANGUAGE)
        assert "Can be used as: target" in result
