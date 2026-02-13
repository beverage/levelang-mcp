"""Pure formatting functions that convert API response dicts into human-readable strings."""

from __future__ import annotations

from typing import Any


def format_translation(response: dict[str, Any]) -> str:
    """Format a translation API response into a readable string.

    Expected response shape:
        {
            "translation": "...",
            "transliteration": "..." | null,
            "transcription": "..." | null,
            "metadata": {
                "source_language": "English",
                "target_language": "French",
                "level": "beginner",
                "level_description": "...",
                "mood": "Casual",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "processing_time_ms": 1250,
            },
            "session_id": "..." | null,
        }
    """
    lines: list[str] = []

    lines.append(f"Translation: {response['translation']}")

    if response.get("transliteration"):
        lines.append(f"Transliteration: {response['transliteration']}")

    if response.get("transcription"):
        lines.append(f"Transcription: {response['transcription']}")

    metadata = response.get("metadata", {})
    if metadata:
        level = metadata.get("level", "")
        level_desc = metadata.get("level_description", "")
        if level and level_desc:
            lines.append(f"Level: {level} ({level_desc})")
        elif level:
            lines.append(f"Level: {level}")

        if metadata.get("mood"):
            lines.append(f"Mood: {metadata['mood']}")

        if metadata.get("mode"):
            lines.append(f"Mode: {metadata['mode']}")

        provider = metadata.get("provider", "")
        model = metadata.get("model", "")
        if provider and model:
            lines.append(f"Provider: {provider} / {model}")
        elif provider:
            lines.append(f"Provider: {provider}")

        if metadata.get("processing_time_ms") is not None:
            lines.append(f"Processing time: {metadata['processing_time_ms']}ms")

    return "\n".join(lines)


def format_language_list(response: dict[str, Any]) -> str:
    """Format a /languages/details response into a readable string.

    Expected response shape:
        {
            "languages": [
                {
                    "code": "fra",
                    "name": "French",
                    "can_be_source": true,
                    "can_be_target": true,
                    "supports_transliteration": false,
                    "levels": [{"code": "beginner", "display_name": "Beginner", ...}, ...],
                    "moods": [{"code": "casual", "display_name": "Casual", ...}, ...],
                }
            ],
            "total_count": 5,
        }
    """
    languages = response.get("languages", [])
    if not languages:
        return "No languages available."

    lines: list[str] = ["Supported Languages:", ""]

    for lang in languages:
        lines.append(f"{lang['name']} ({lang['code']})")

        # Levels
        levels = lang.get("levels", [])
        if levels:
            level_names = [lv.get("display_name", lv.get("code", "")) for lv in levels]
            lines.append(f"  Levels: {', '.join(level_names)}")

        # Moods
        moods = lang.get("moods", [])
        if moods:
            mood_names = [m.get("display_name", m.get("code", "")) for m in moods]
            lines.append(f"  Moods: {', '.join(mood_names)}")

        # Modes
        modes = lang.get("modes", [])
        if modes:
            mode_names = [m.get("display_name", m.get("code", "")) for m in modes]
            lines.append(f"  Modes: {', '.join(mode_names)}")

        # Source/target
        roles: list[str] = []
        if lang.get("can_be_source"):
            roles.append("source")
        if lang.get("can_be_target"):
            roles.append("target")
        if roles:
            lines.append(f"  Can be: {', '.join(roles)}")

        lines.append("")  # blank line between languages

    return "\n".join(lines).rstrip()


def format_language_detail(language: dict[str, Any]) -> str:
    """Format a single /languages/{code} response into a readable string.

    Same shape as one entry in the /languages/details response.
    """
    lines: list[str] = [f"{language['name']} ({language['code']})", ""]

    # Levels with descriptions
    levels = language.get("levels", [])
    if levels:
        lines.append("Proficiency Levels:")
        for lv in levels:
            name = lv.get("display_name", lv.get("code", ""))
            desc = lv.get("description", "")
            if desc:
                lines.append(f"  {name}: {desc}")
            else:
                lines.append(f"  {name}")
        lines.append("")

    # Moods with descriptions
    moods = language.get("moods", [])
    if moods:
        lines.append("Moods:")
        for m in moods:
            name = m.get("display_name", m.get("code", ""))
            desc = m.get("description", "")
            default_marker = " (default)" if m.get("is_default") else ""
            if desc:
                lines.append(f"  {name}{default_marker}: {desc}")
            else:
                lines.append(f"  {name}{default_marker}")
        lines.append("")

    # Modes with descriptions
    modes = language.get("modes", [])
    if modes:
        lines.append("Modes:")
        for m in modes:
            name = m.get("display_name", m.get("code", ""))
            desc = m.get("description", "")
            default_marker = " (default)" if m.get("is_default") else ""
            if desc:
                lines.append(f"  {name}{default_marker}: {desc}")
            else:
                lines.append(f"  {name}{default_marker}")
        lines.append("")

    # Source/target
    roles: list[str] = []
    if language.get("can_be_source"):
        roles.append("source")
    if language.get("can_be_target"):
        roles.append("target")
    if roles:
        lines.append(f"Can be used as: {', '.join(roles)}")

    return "\n".join(lines)


def format_comparison(
    text: str,
    language_name: str,
    mood: str,
    results: list[dict[str, Any]],
    mode: str | None = None,
) -> str:
    """Format a side-by-side comparison of translations at all proficiency levels.

    Args:
        text: The original source text.
        language_name: Human-readable language name (e.g. "French").
        mood: The mood used for all translations.
        results: List of dicts with keys:
            - level: str (level code)
            - ok: bool
            - result: dict (translation response, if ok)
            - error: str (error message, if not ok)
        mode: The mode used for all translations (e.g. "spoken", "written").
            Omitted from the header when None or "written".
    """
    header = f"Language: {language_name} | Mood: {mood.capitalize()}"
    if mode and mode != "written":
        header += f" | Mode: {mode.capitalize()}"

    lines: list[str] = [
        f'Comparing translations of: "{text}"',
        header,
        "",
    ]

    for entry in results:
        level = entry["level"].capitalize()
        lines.append(f"── {level} ──")

        if not entry["ok"]:
            lines.append(f"  Error: {entry['error']}")
        else:
            result = entry["result"]
            lines.append(result.get("translation", "(no translation)"))

            if result.get("transliteration"):
                lines.append(f"  Transliteration: {result['transliteration']}")

            metadata = result.get("metadata", {})
            processing_time = metadata.get("processing_time_ms")
            if processing_time is not None:
                lines.append(f"  ({processing_time:.0f}ms)")

        lines.append("")

    return "\n".join(lines).rstrip()
