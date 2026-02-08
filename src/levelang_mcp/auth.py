"""Lightweight API-key authentication middleware for streamable-http."""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


logger = logging.getLogger("levelang_mcp.auth")

# Paths that bypass authentication (e.g. health checks for load balancers).
_PUBLIC_PATHS: frozenset[str] = frozenset({"/health"})


async def health_endpoint(request: Request) -> JSONResponse:
    """Unauthenticated health-check endpoint for load balancers."""
    return JSONResponse({"status": "ok"})


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Validate ``Authorization: Bearer <key>`` against a set of known keys.

    When *valid_keys* is empty, every request is allowed through (auth
    disabled).  This lets local development work without configuring keys.

    Requests to paths in ``_PUBLIC_PATHS`` (e.g. ``/health``) are always
    allowed through regardless of auth configuration.
    """

    def __init__(self, app: object, valid_keys: frozenset[str]) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.valid_keys = valid_keys

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Public paths bypass auth entirely.
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # Auth disabled — pass everything through.
        if not self.valid_keys:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(
                "Auth failed: missing Authorization header (client=%s)", client_ip
            )
            return JSONResponse(
                {"error": "Missing Authorization header"},
                status_code=401,
            )

        # Expect "Bearer <key>"
        parts = auth_header.split(" ", maxsplit=1)
        if len(parts) != 2 or parts[0] != "Bearer":
            logger.warning(
                "Auth failed: malformed Authorization header (client=%s)", client_ip
            )
            return JSONResponse(
                {
                    "error": "Invalid Authorization header format, expected 'Bearer <key>'"
                },
                status_code=401,
            )

        key = parts[1]
        if key not in self.valid_keys:
            logger.warning("Auth failed: invalid API key (client=%s)", client_ip)
            return JSONResponse(
                {"error": "Invalid API key"},
                status_code=401,
            )

        return await call_next(request)
