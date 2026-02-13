"""Sample API response data for tests."""

SAMPLE_TRANSLATION_RESPONSE = {
    "translation": "Bonjour le monde",
    "transliteration": None,
    "transcription": None,
    "metadata": {
        "source_language": "English",
        "target_language": "French",
        "source_code": "eng",
        "target_code": "fra",
        "level": "A2",
        "level_description": "elementary proficiency",
        "mood": "Casual",
        "mode": "Written",
        "provider": "gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.1,
        "processing_time_ms": 800,
    },
    "session_id": "abc-123",
}

SAMPLE_TRANSLATION_WITH_TRANSLIT = {
    "translation": "\u4f60\u597d\u4e16\u754c",
    "transliteration": "n\u01d0 h\u01ceo sh\u00ec ji\u00e8",
    "transcription": None,
    "metadata": {
        "source_language": "English",
        "target_language": "Mandarin Chinese",
        "source_code": "eng",
        "target_code": "cmn",
        "level": "HSK1",
        "level_description": "basic vocabulary",
        "mood": "Casual",
        "mode": "Written",
        "provider": "gemini",
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.1,
        "processing_time_ms": 950,
    },
    "session_id": None,
}

SAMPLE_LANGUAGES_RESPONSE = {
    "languages": [
        {
            "code": "fra",
            "name": "French",
            "can_be_source": False,
            "can_be_target": True,
            "supports_transliteration": False,
            "levels": [
                {
                    "code": "beginner",
                    "display_name": "Beginner",
                    "description": "Basic vocabulary",
                },
                {
                    "code": "intermediate",
                    "display_name": "Intermediate",
                    "description": "Complex structures",
                },
                {
                    "code": "advanced",
                    "display_name": "Advanced",
                    "description": "Full grammar",
                },
                {
                    "code": "fluent",
                    "display_name": "Fluent",
                    "description": "Native equivalent",
                },
            ],
            "moods": [
                {"code": "casual", "display_name": "Casual", "is_default": True},
                {"code": "polite", "display_name": "Polite", "is_default": False},
                {"code": "formal", "display_name": "Formal", "is_default": False},
            ],
            "modes": [
                {"code": "written", "display_name": "Written", "is_default": True},
                {"code": "spoken", "display_name": "Spoken", "is_default": False},
            ],
        },
        {
            "code": "cmn",
            "name": "Mandarin Chinese",
            "can_be_source": False,
            "can_be_target": True,
            "supports_transliteration": True,
            "levels": [
                {
                    "code": "beginner",
                    "display_name": "Beginner",
                    "description": "Basic vocabulary",
                },
                {
                    "code": "intermediate",
                    "display_name": "Intermediate",
                    "description": "Complex structures",
                },
            ],
            "moods": [
                {"code": "casual", "display_name": "Casual", "is_default": True},
            ],
            "modes": [],
        },
    ],
    "total_count": 2,
}

SAMPLE_SINGLE_LANGUAGE = {
    "code": "fra",
    "name": "French",
    "can_be_source": False,
    "can_be_target": True,
    "supports_transliteration": False,
    "levels": [
        {
            "code": "beginner",
            "display_name": "Beginner",
            "description": "Basic vocabulary",
        },
        {
            "code": "intermediate",
            "display_name": "Intermediate",
            "description": "Complex structures",
        },
    ],
    "moods": [
        {
            "code": "casual",
            "display_name": "Casual",
            "is_default": True,
            "description": "Everyday conversation",
        },
        {
            "code": "formal",
            "display_name": "Formal",
            "is_default": False,
            "description": "Professional contexts",
        },
    ],
    "modes": [
        {
            "code": "written",
            "display_name": "Written",
            "is_default": True,
            "description": "Standard written French as taught in textbooks",
        },
        {
            "code": "spoken",
            "display_name": "Spoken",
            "is_default": False,
            "description": "How native French speakers actually talk in everyday conversation",
        },
    ],
}
