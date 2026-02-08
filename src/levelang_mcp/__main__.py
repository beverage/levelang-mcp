"""Entrypoint for running the Levelang MCP server.

Usage:
    python -m levelang_mcp
"""

from .server import mcp, settings


def main() -> None:
    transport = settings.mcp_transport
    if transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


main()
