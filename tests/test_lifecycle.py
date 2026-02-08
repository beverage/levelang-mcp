"""Tests for client lifecycle and graceful shutdown."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from levelang_mcp.__main__ import _resolve_log_format
from levelang_mcp.client import LevelangClient


# ---------------------------------------------------------------------------
# Async context manager tests
# ---------------------------------------------------------------------------


class TestClientContextManager:
    async def test_enter_returns_self(self):
        client = LevelangClient()
        async with client as ctx:
            assert ctx is client

    async def test_exit_closes_client(self):
        client = LevelangClient()
        client.close = AsyncMock()  # type: ignore[method-assign]
        async with client:
            pass
        client.close.assert_awaited_once()

    async def test_exit_closes_on_exception(self):
        client = LevelangClient()
        client.close = AsyncMock()  # type: ignore[method-assign]
        with patch.object(client, "close", new_callable=AsyncMock) as mock_close:
            try:
                async with client:
                    raise RuntimeError("boom")
            except RuntimeError:
                pass
            mock_close.assert_awaited_once()


# ---------------------------------------------------------------------------
# Log format resolution tests
# ---------------------------------------------------------------------------


class TestResolveLogFormat:
    def test_auto_resolves_to_json_for_http(self):
        assert _resolve_log_format("auto", "streamable-http") == "json"

    def test_auto_resolves_to_text_for_stdio(self):
        assert _resolve_log_format("auto", "stdio") == "text"

    def test_explicit_json_preserved(self):
        assert _resolve_log_format("json", "stdio") == "json"

    def test_explicit_text_preserved(self):
        assert _resolve_log_format("text", "streamable-http") == "text"
