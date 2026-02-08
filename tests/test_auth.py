"""Tests for API-key authentication middleware and config parsing."""

from __future__ import annotations

import logging

import pytest

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from levelang_mcp.auth import APIKeyAuthMiddleware, health_endpoint
from levelang_mcp.config import _parse_api_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_KEYS = frozenset({"key-alpha", "key-beta"})


def _echo_app(*, include_health: bool = False) -> Starlette:
    """Tiny Starlette app that echoes 'ok' — used as the inner app."""

    async def homepage(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("healthy")

    routes: list[Route] = [Route("/", homepage, methods=["GET", "POST", "DELETE"])]
    if include_health:
        routes.append(Route("/health", health))
    return Starlette(routes=routes)


def _client_with_keys(
    keys: frozenset[str],
    *,
    include_health: bool = False,
) -> TestClient:
    app = _echo_app(include_health=include_health)
    app.add_middleware(APIKeyAuthMiddleware, valid_keys=keys)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Middleware tests
# ---------------------------------------------------------------------------


class TestAPIKeyAuthMiddleware:
    def test_rejects_missing_authorization_header(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/")
        assert resp.status_code == 401
        assert "Missing Authorization header" in resp.json()["error"]

    def test_rejects_malformed_authorization_header(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Basic abc123"})
        assert resp.status_code == 401
        assert "Invalid Authorization header format" in resp.json()["error"]

    def test_rejects_bearer_without_key(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearer"})
        assert resp.status_code == 401
        assert "Invalid Authorization header format" in resp.json()["error"]

    def test_rejects_invalid_key(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401
        assert "Invalid API key" in resp.json()["error"]

    def test_accepts_valid_key(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearer key-alpha"})
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_accepts_second_valid_key(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearer key-beta"})
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_auth_disabled_when_no_keys(self):
        client = _client_with_keys(frozenset())
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_auth_disabled_allows_any_header(self):
        client = _client_with_keys(frozenset())
        resp = client.get("/", headers={"Authorization": "Bearer garbage"})
        assert resp.status_code == 200

    def test_bearer_is_case_sensitive(self):
        """'bearer' and 'BEARER' should be rejected — only 'Bearer' is valid."""
        client = _client_with_keys(VALID_KEYS)
        for scheme in ("bearer", "BEARER", "bEaReR"):
            resp = client.get("/", headers={"Authorization": f"{scheme} key-alpha"})
            assert resp.status_code == 401, f"Scheme '{scheme}' should be rejected"

    def test_rejects_empty_bearer_value(self):
        """'Bearer ' (trailing space, empty key) should be rejected."""
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401

    def test_rejects_authorization_header_without_space(self):
        """'Bearerkey-alpha' (no space) should be rejected."""
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/", headers={"Authorization": "Bearerkey-alpha"})
        assert resp.status_code == 401

    def test_works_with_post_method(self):
        """MCP uses POST — verify auth works for POST, not just GET."""
        client = _client_with_keys(VALID_KEYS)
        resp = client.post("/", headers={"Authorization": "Bearer key-alpha"})
        assert resp.status_code == 200

    def test_post_rejected_without_auth(self):
        client = _client_with_keys(VALID_KEYS)
        resp = client.post("/")
        assert resp.status_code == 401

    def test_401_response_is_json(self):
        """All 401 responses should have JSON content type."""
        client = _client_with_keys(VALID_KEYS)
        resp = client.get("/")
        assert resp.status_code == 401
        assert "application/json" in resp.headers["content-type"]
        assert "error" in resp.json()

    def test_single_key_set(self):
        """Auth works when only one key is configured."""
        client = _client_with_keys(frozenset({"only-key"}))
        resp = client.get("/", headers={"Authorization": "Bearer only-key"})
        assert resp.status_code == 200
        resp = client.get("/", headers={"Authorization": "Bearer other-key"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Config parsing tests
# ---------------------------------------------------------------------------


class TestParseAPIKeys:
    def test_none_returns_empty(self):
        assert _parse_api_keys(None) == frozenset()

    def test_empty_string_returns_empty(self):
        assert _parse_api_keys("") == frozenset()

    def test_whitespace_only_returns_empty(self):
        assert _parse_api_keys("   ") == frozenset()

    def test_single_key(self):
        assert _parse_api_keys("abc123") == frozenset({"abc123"})

    def test_multiple_keys(self):
        assert _parse_api_keys("a,b,c") == frozenset({"a", "b", "c"})

    def test_strips_whitespace(self):
        assert _parse_api_keys(" a , b , c ") == frozenset({"a", "b", "c"})

    def test_filters_empty_entries(self):
        assert _parse_api_keys("a,,b,,,c") == frozenset({"a", "b", "c"})

    def test_settings_integration(self, monkeypatch: pytest.MonkeyPatch):
        """MCP_API_KEYS env var flows through to settings."""
        monkeypatch.setenv("MCP_API_KEYS", "key1,key2")

        from levelang_mcp.config import get_settings, reset_settings

        reset_settings()
        s = get_settings()
        assert s.mcp_api_keys == frozenset({"key1", "key2"})


# ---------------------------------------------------------------------------
# Health check bypass tests
# ---------------------------------------------------------------------------


class TestHealthCheckBypass:
    def test_health_bypasses_auth(self):
        client = _client_with_keys(VALID_KEYS, include_health=True)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_bypasses_auth_no_header(self):
        """Health check works even with no Authorization header at all."""
        client = _client_with_keys(VALID_KEYS, include_health=True)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "healthy"

    def test_non_health_still_requires_auth(self):
        """Other paths still require auth when keys are configured."""
        client = _client_with_keys(VALID_KEYS, include_health=True)
        resp = client.get("/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Auth failure logging tests
# ---------------------------------------------------------------------------


class TestAuthLogging:
    def test_logs_missing_header(self, caplog: pytest.LogCaptureFixture):
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/")
        assert any("missing Authorization header" in r.message for r in caplog.records)

    def test_logs_malformed_header(self, caplog: pytest.LogCaptureFixture):
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/", headers={"Authorization": "Basic xyz"})
        assert any(
            "malformed Authorization header" in r.message for r in caplog.records
        )

    def test_logs_invalid_key(self, caplog: pytest.LogCaptureFixture):
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/", headers={"Authorization": "Bearer bad-key"})
        assert any("invalid API key" in r.message for r in caplog.records)

    def test_no_log_on_success(self, caplog: pytest.LogCaptureFixture):
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/", headers={"Authorization": "Bearer key-alpha"})
        assert not any("Auth failed" in r.message for r in caplog.records)

    def test_log_includes_client_ip(self, caplog: pytest.LogCaptureFixture):
        """Log messages should include the client address for debugging."""
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/")
        auth_records = [r for r in caplog.records if "Auth failed" in r.message]
        assert len(auth_records) == 1
        assert "client=" in auth_records[0].message

    def test_no_log_on_health_check(self, caplog: pytest.LogCaptureFixture):
        """Health check requests should not produce auth log entries."""
        client = _client_with_keys(VALID_KEYS, include_health=True)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/health")
        assert not any("Auth failed" in r.message for r in caplog.records)

    def test_key_not_leaked_in_log(self, caplog: pytest.LogCaptureFixture):
        """The actual API key should never appear in log messages."""
        client = _client_with_keys(VALID_KEYS)
        with caplog.at_level(logging.WARNING, logger="levelang_mcp.auth"):
            client.get("/", headers={"Authorization": "Bearer secret-key-value"})
        for record in caplog.records:
            assert "secret-key-value" not in record.message


# ---------------------------------------------------------------------------
# Config defaults tests
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    def test_mcp_api_keys_defaults_to_empty(self, monkeypatch: pytest.MonkeyPatch):
        """When MCP_API_KEYS is not set, mcp_api_keys should be empty."""
        monkeypatch.delenv("MCP_API_KEYS", raising=False)

        from levelang_mcp.config import get_settings, reset_settings

        reset_settings()
        s = get_settings()
        assert s.mcp_api_keys == frozenset()

    def test_mcp_transport_defaults_to_stdio(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)

        from levelang_mcp.config import get_settings, reset_settings

        reset_settings()
        s = get_settings()
        assert s.mcp_transport == "stdio"

    def test_mcp_port_defaults_to_8463(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("MCP_PORT", raising=False)

        from levelang_mcp.config import get_settings, reset_settings

        reset_settings()
        s = get_settings()
        assert s.mcp_port == 8463


# ---------------------------------------------------------------------------
# Health endpoint response tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Test the actual health_endpoint handler from auth.py."""

    @staticmethod
    def _client_with_real_health(keys: frozenset[str]) -> TestClient:
        app = Starlette(routes=[Route("/health", health_endpoint)])
        app.add_middleware(APIKeyAuthMiddleware, valid_keys=keys)
        return TestClient(app, raise_server_exceptions=False)

    def test_health_returns_json_body(self):
        client = self._client_with_real_health(VALID_KEYS)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_content_type_is_json(self):
        client = self._client_with_real_health(VALID_KEYS)
        resp = client.get("/health")
        assert "application/json" in resp.headers["content-type"]

    def test_health_bypasses_auth_with_real_handler(self):
        client = self._client_with_real_health(VALID_KEYS)
        resp = client.get("/health")
        assert resp.status_code == 200
