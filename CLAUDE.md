# Levelang MCP Server

Stateless MCP server that exposes the Levelang translation API to AI assistants. Translates MCP tool calls into HTTP requests to the backend. This is the dev-workflow MCP: Claude Code spawns it over stdio via the constellation's `.mcp.json`. End users use `levelang-mcp-app` instead (DEC-021).

## Tech Stack

- **Framework**: Python MCP SDK
- **Package manager**: uv
- **Transport**: stdio (local) or streamable-http (deployed)
- **Deployment**: Fly.io, region `cdg`, port 8080

## Architecture

No database, no shared state, no code shared with the backend.

```
src/levelang_mcp/
├── __main__.py       # Entrypoint (python -m levelang_mcp)
├── server.py         # MCP tools and resources definitions
├── auth.py           # API-key auth middleware for HTTP transport
├── client.py         # Async HTTP client for the Levelang backend API
├── config.py         # Environment variable loading
├── formatting.py     # API response → human-readable text for LLMs
└── logging_config.py # Logging setup
```

## Key Coupling Points

- `client.py` — Makes HTTP calls to the backend. Must stay in sync with backend API endpoints and response schemas.
- `formatting.py` — Formats backend JSON into human-readable text for the LLM. Must stay in sync with the backend translate response schema.
- `server.py` — Defines MCP tools (`translate`, `translate_compare`, `list_languages`), resources (`levelang://languages`, `levelang://languages/{code}`) and the `compare_levels` prompt.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LEVELANG_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend URL |
| `LEVELANG_API_KEY` | — | Service key (`sk_*`) for backend auth |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP transport |
| `MCP_PORT` | `8463` | Port for HTTP transport |
| `MCP_API_KEYS` | — | Comma-separated client auth keys for HTTP |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_FORMAT` | `auto` | `auto` (JSON for HTTP, text for stdio), `json` or `text` |

## Commands

```bash
uv sync                              # Install dependencies
uv run pytest tests/ -v              # Run tests
git config core.hooksPath .githooks  # Enable pre-commit/pre-push hooks
```
