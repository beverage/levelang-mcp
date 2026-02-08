"""Entrypoint for running the Levelang MCP server.

Usage:
    python -m levelang_mcp
"""

from __future__ import annotations

import logging

import anyio

from starlette.routing import Route

from .auth import APIKeyAuthMiddleware, health_endpoint
from .logging_config import setup_logging
from .server import levelang, mcp, settings


logger = logging.getLogger("levelang_mcp.server")


def _resolve_log_format(raw: str, transport: str) -> str:
    """Resolve ``"auto"`` to a concrete format based on transport."""
    if raw == "auto":
        return "json" if transport == "streamable-http" else "text"
    return raw


async def _run_streamable_http() -> None:
    """Start the streamable-http transport with API-key auth middleware."""
    import uvicorn

    app = mcp.streamable_http_app()

    # Add the health-check route (bypasses auth via _PUBLIC_PATHS).
    app.routes.append(Route("/health", health_endpoint))

    app.add_middleware(APIKeyAuthMiddleware, valid_keys=settings.mcp_api_keys)

    host = mcp.settings.host
    port = mcp.settings.port

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        # Disable uvicorn's access log — app-level logging is sufficient
        # and avoids noisy per-request lines for MCP's JSON-RPC traffic.
        access_log=False,
        # Don't advertise the server implementation in response headers.
        server_header=False,
        # Keep-alive timeout — how long to keep idle connections open.
        # MCP clients may hold long-lived connections; 120s is generous
        # without being wasteful.
        timeout_keep_alive=120,
        # Graceful shutdown timeout — how long to wait for in-flight
        # requests to finish before forcing a shutdown.
        timeout_graceful_shutdown=30,
    )
    server = uvicorn.Server(config)

    logger.info("Listening on %s:%d (transport=streamable-http)", host, port)

    try:
        await server.serve()
    finally:
        logger.info("Shutting down — closing HTTP client")
        await levelang.close()


def main() -> None:
    transport = settings.mcp_transport
    log_format = _resolve_log_format(settings.log_format, transport)
    setup_logging(log_level=settings.log_level, log_format=log_format)

    logger.info("Starting Levelang MCP server (transport=%s)", transport)

    if transport == "streamable-http":
        anyio.run(_run_streamable_http)
    else:
        try:
            mcp.run(transport="stdio")
        finally:
            # stdio runs its own event loop; run async cleanup separately.
            anyio.run(levelang.close)


if __name__ == "__main__":
    main()
