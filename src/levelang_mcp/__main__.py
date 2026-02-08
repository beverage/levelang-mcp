"""Entrypoint for running the Levelang MCP server.

Usage:
    python -m levelang_mcp
"""

from __future__ import annotations

import anyio

from starlette.routing import Route

from .auth import APIKeyAuthMiddleware, health_endpoint
from .server import mcp, settings


async def _run_streamable_http() -> None:
    """Start the streamable-http transport with API-key auth middleware."""
    import uvicorn

    app = mcp.streamable_http_app()

    # Add the health-check route (bypasses auth via _PUBLIC_PATHS).
    app.routes.append(Route("/health", health_endpoint))

    app.add_middleware(APIKeyAuthMiddleware, valid_keys=settings.mcp_api_keys)

    config = uvicorn.Config(
        app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    transport = settings.mcp_transport
    if transport == "streamable-http":
        anyio.run(_run_streamable_http)
    else:
        mcp.run(transport="stdio")


main()
