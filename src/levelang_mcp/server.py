"""Levelang MCP Server -- tools and resources."""

from __future__ import annotations

import asyncio

import httpx

from mcp.server.fastmcp import FastMCP

from .client import LevelangClient
from .config import get_settings
from .formatting import (
    format_comparison,
    format_language_detail,
    format_language_list,
    format_translation,
)


def _sanitize_text(text: str) -> str:
    """Light sanitization of input text before sending to the backend.

    Strips leading/trailing whitespace only. Does NOT collapse internal
    newlines -- multi-line input (poems, paragraphs) is legitimate and
    should be preserved. The backend is responsible for handling newlines
    safely when constructing LLM prompts and parsing responses.
    """
    return text.strip()


settings = get_settings()

mcp = FastMCP(
    "Levelang",
    instructions="AI-powered translation at learner-appropriate proficiency levels. "
    "Use the translate tool to translate text at a specific proficiency level, "
    "and list_languages to discover available languages, levels, moods, and modes.",
    host=settings.mcp_host,
    port=settings.mcp_port,
)

levelang = LevelangClient()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def translate(
    text: str,
    target_language: str,
    level: str,
    source_language: str = "eng",
    mood: str = "casual",
    mode: str | None = None,
) -> str:
    """Translate text to a target language at a specific proficiency level.

    Unlike standard translators that produce native-speaker complexity,
    this translates at the learner's level -- beginner translations use
    simple grammar, intermediate uses more complex structures, etc.

    Args:
        text: The text to translate (any length, any source language)
        target_language: Target language code -- use list_languages to see
            available codes (e.g. fra, deu, cmn, yue, ita)
        level: Proficiency level -- proficiency levels available for the target language (e.g. beginner, intermediate, advanced, and/or fluent)
        source_language: Source language code (default: eng for English)
        mood: Tone -- tones available for the target language
        mode: Language mode (spoken/written) -- controls whether the
            translation targets written or spoken register. Use
            list_languages to see available modes per language.

    Returns:
        The translated text with metadata about the translation.
    """
    try:
        result = await levelang.translate(
            text=_sanitize_text(text),
            source_language_code=source_language,
            target_language_code=target_language,
            level=level,
            mood=mood,
            mode=mode,
        )
        return format_translation(result)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            detail = e.response.json().get("detail", "Validation error")
            return f"Invalid request: {detail}"
        elif e.response.status_code == 429:
            return "Rate limit reached. Please wait a moment and try again."
        elif e.response.status_code >= 500:
            return "Translation service is temporarily unavailable. Please try again."
        else:
            return f"Backend error (HTTP {e.response.status_code}): {e.response.text}"
    except httpx.TimeoutException:
        return "Translation request timed out. The backend may be under heavy load."
    except httpx.ConnectError:
        return "Cannot reach the Levelang backend. Check that the service is running."
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def list_languages() -> str:
    """List all languages supported by Levelang with their available levels and moods.

    Use this to discover valid language codes, proficiency levels, mood
    options, and mode options before calling the translate tool.

    Returns:
        Formatted list of supported languages and their configurations.
    """
    try:
        result = await levelang.get_languages()
        return format_language_list(result)
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            return "Language service is temporarily unavailable. Please try again."
        return f"Backend error (HTTP {e.response.status_code}): {e.response.text}"
    except httpx.TimeoutException:
        return "Request timed out while fetching languages."
    except httpx.ConnectError:
        return "Cannot reach the Levelang backend. Check that the service is running."
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def translate_compare(
    text: str,
    target_language: str,
    source_language: str = "eng",
    mood: str = "casual",
    levels: list[str] | None = None,
    mode: str | None = None,
) -> str:
    """Translate text at multiple proficiency levels to compare complexity differences.

    Shows how the same text is translated differently at different levels --
    useful for understanding how grammar and vocabulary constraints change
    across proficiency.

    Args:
        text: The text to translate (any length, any source language)
        target_language: Target language code -- use list_languages to see
            available codes (e.g. fra, deu, cmn, yue, ita)
        source_language: Source language code (default: eng for English)
        mood: Tone -- tones available for the target language
        levels: Optional list of proficiency level codes to compare
            (e.g. ["beginner", "advanced"]). If omitted, compares all
            available levels. Use list_languages to see valid codes per language.
        mode: Optional language mode (spoken/written) -- controls whether the
            translation targets written or spoken register. If omitted, compares
            all available levels. Use list_languages to see valid codes per language.

    Returns:
        The same text translated at each requested level, formatted for comparison.
    """
    sanitized = _sanitize_text(text)

    # Fetch available levels for this language
    try:
        lang_config = await levelang.get_language(target_language)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Language '{target_language}' not found. Use list_languages to see available codes."
        return f"Backend error (HTTP {e.response.status_code}): {e.response.text}"
    except httpx.ConnectError:
        return "Cannot reach the Levelang backend. Check that the service is running."
    except httpx.TimeoutException:
        return "Request timed out while fetching language details."
    except Exception as e:
        return f"Unexpected error: {e}"

    available_levels = lang_config.get("levels", [])
    if not available_levels:
        return f"No proficiency levels configured for '{target_language}'."

    available_codes = [lv.get("code", "") for lv in available_levels if lv.get("code")]

    if levels is not None:
        invalid = [lv for lv in levels if lv not in available_codes]
        if invalid:
            return (
                f"Invalid level(s): {', '.join(invalid)}. "
                f"Available levels for '{target_language}': {', '.join(available_codes)}"
            )
        level_codes = levels
    else:
        level_codes = available_codes

    # Translate at requested levels concurrently
    async def _translate_at_level(level: str) -> dict:
        try:
            result = await levelang.translate(
                text=sanitized,
                source_language_code=source_language,
                target_language_code=target_language,
                level=level,
                mood=mood,
                mode=mode,
            )
            return {"level": level, "ok": True, "result": result}
        except Exception as e:
            return {"level": level, "ok": False, "error": str(e)}

    results = await asyncio.gather(*[_translate_at_level(lv) for lv in level_codes])

    return format_comparison(
        text=sanitized,
        language_name=lang_config.get("name", target_language),
        mood=mood,
        results=list(results),
        mode=mode,
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("levelang://languages")
async def languages_resource() -> str:
    """List of all supported languages with their levels and moods."""
    try:
        result = await levelang.get_languages()
        return format_language_list(result)
    except Exception:
        return "Unable to fetch language list from the backend."


@mcp.resource("levelang://languages/{language_code}")
async def language_detail_resource(language_code: str) -> str:
    """Detailed configuration for a specific language including level descriptions."""
    try:
        result = await levelang.get_language(language_code)
        return format_language_detail(result)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Language '{language_code}' not found."
        return f"Error fetching language details: {e.response.text}"
    except Exception:
        return f"Unable to fetch details for language '{language_code}'."


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def compare_levels(language: str = "French") -> str:
    """Create a prompt for comparing how the same text is translated at different levels.

    Args:
        language: Target language name
    """
    return f"""The user will provide a sentence or short text.
Please translate it into {language} at all available levels using the
translate_compare tool. If the user specifies particular levels to compare,
pass them via the levels parameter; otherwise omit it to compare all levels.
If the user specifies a mode (spoken or written), pass it via the mode
parameter; otherwise omit it to use the language's default mode.

After all translations, provide a brief analysis of what grammatical
features change between levels and why."""
