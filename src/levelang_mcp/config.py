"""Configuration loading from environment variables."""

from __future__ import annotations

import os

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    api_base_url: str
    api_key: str | None
    mcp_transport: str
    mcp_port: int


_settings: Settings | None = None


def get_settings() -> Settings:
    """Load settings from environment variables (cached after first call)."""
    global _settings
    if _settings is not None:
        return _settings

    _settings = Settings(
        api_base_url=os.environ.get(
            "LEVELANG_API_BASE_URL",
            "http://localhost:8000/api/v1",
        ),
        api_key=os.environ.get("LEVELANG_API_KEY"),
        mcp_transport=os.environ.get("MCP_TRANSPORT", "stdio"),
        mcp_port=int(os.environ.get("MCP_PORT", "8080")),
    )
    return _settings


def reset_settings() -> None:
    """Reset cached settings (useful for testing)."""
    global _settings
    _settings = None
