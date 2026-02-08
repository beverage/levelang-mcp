"""Configuration loading from environment variables."""

from __future__ import annotations

import os

from dataclasses import dataclass

from dotenv import load_dotenv


# Load .env once at import time.  Existing environment variables take
# precedence over values defined in .env (the python-dotenv default).
load_dotenv()


def _parse_api_keys(raw: str | None) -> frozenset[str]:
    """Parse a comma-separated list of API keys into a frozenset.

    Strips whitespace from each key and discards empty strings.
    Returns an empty frozenset when *raw* is ``None`` or blank,
    which signals that auth is disabled.
    """
    if not raw:
        return frozenset()
    return frozenset(k for k in (k.strip() for k in raw.split(",")) if k)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    api_base_url: str
    api_key: str | None
    mcp_transport: str
    mcp_host: str
    mcp_port: int
    mcp_api_keys: frozenset[str]
    log_level: str
    log_format: str


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
        mcp_host=os.environ.get("MCP_HOST", "127.0.0.1"),
        mcp_port=int(os.environ.get("MCP_PORT", "8463")),
        mcp_api_keys=_parse_api_keys(os.environ.get("MCP_API_KEYS")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        log_format=os.environ.get("LOG_FORMAT", "auto"),
    )
    return _settings


def reset_settings() -> None:
    """Reset cached settings (useful for testing)."""
    global _settings
    _settings = None
