"""Shared fixtures for Levelang MCP tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_settings():
    """Reset cached settings before each test so env var changes take effect."""
    from levelang_mcp.config import reset_settings

    reset_settings()
    yield
    reset_settings()


@pytest.fixture(autouse=True)
def _set_default_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure a known baseline of env vars for all tests."""
    monkeypatch.setenv("LEVELANG_API_BASE_URL", "http://testserver/api/v1")
    # No LEVELANG_API_KEY by default (matches local-dev experience)
    monkeypatch.delenv("LEVELANG_API_KEY", raising=False)
