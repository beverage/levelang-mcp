# levelang.app MCP Server

[![CI](https://github.com/beverage/levelang-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/beverage/levelang-mcp/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP SDK](https://img.shields.io/badge/MCP%20SDK-1.26-purple.svg)](https://modelcontextprotocol.io/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet.svg)](https://docs.astral.sh/uv/)

An [MCP](https://modelcontextprotocol.io/) server that exposes the [levelang.app](https://levelang.app) translation API to AI assistants. Unlike standard translators that always produce native-speaker complexity, levelang.app constrains translations to the learner's proficiency level.

---

## Features

- **Level-Aware Translation** — Translate text at beginner, intermediate, advanced, or fluent proficiency with grammar constraints enforced per level
- **Multi-Language Support** — French, German, Italian, Mandarin Chinese, Cantonese, with transliteration where applicable
- **Mood Control** — Casual, polite, and formal translation styles
- **Language Discovery** — Query available languages, levels, and moods dynamically from the backend
- **MCP Resources** — `levelang://languages` and `levelang://languages/{code}` for pulling language configs into context
- **Stateless Wrapper** — No database, no shared state; translates MCP tool calls into backend HTTP requests

## Quick Start

**Prerequisites**: Python 3.12+, [uv](https://docs.astral.sh/uv/), a running [Levelang backend](https://github.com/beverage/levelang-backend) (local or remote)

```bash
git clone https://github.com/beverage/levelang-mcp.git
cd levelang-mcp
uv sync
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "levelang": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/absolute/path/to/levelang-mcp",
        "python", "-m", "levelang_mcp"
      ],
      "env": {
        "LEVELANG_API_BASE_URL": "http://localhost:8000/api/v1",
        "LEVELANG_API_KEY": "sk_your_service_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. A hammer icon in the chat input indicates MCP tools are available.

The same configuration works for **Cursor** (`.cursor/mcp.json`) and **Claude Code**.

### Example Usage

Once connected, ask your AI assistant things like:

> Translate "I would like to order a coffee, please" into French at the beginner level.

> What languages does Levelang support?

> Compare how "I'm worried the new rules might prevent us from finishing on time" translates into German at beginner vs advanced level.

## Configuration

All configuration is through environment variables, set in the `env` block of your MCP client config.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEVELANG_API_BASE_URL` | No | `http://localhost:8000/api/v1` | Levelang backend URL |
| `LEVELANG_API_KEY` | Depends | — | Service key (`sk_xxx`) for backend auth |
| `MCP_TRANSPORT` | No | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | No | `8463` | Port when using HTTP transport |
| `MCP_API_KEYS` | No | — | Comma-separated valid API keys for HTTP auth |

`LEVELANG_API_KEY` is required when connecting to a remote backend (staging/production). It may be omitted for local development if the backend has auth disabled.

`MCP_API_KEYS` controls client authentication for the HTTP transport. When set, clients must send `Authorization: Bearer <key>` with a key from this list. When empty or unset, auth is disabled (open access). This has no effect on stdio transport.

> **Note:** This is a simple static-key scheme suited to small-scale and internal use. For higher-scale needs (many users, per-key revocation, usage tracking), swap in database-backed keys or an auth provider — the middleware pattern and client config remain the same.

**Local development** (no auth):
```json
"env": { "LEVELANG_API_BASE_URL": "http://localhost:8000/api/v1" }
```

**Staging** (requires service key):
```json
"env": {
  "LEVELANG_API_BASE_URL": "",
  "LEVELANG_API_KEY": ""
}
```

### Remote HTTP Connection

When the MCP server is running in `streamable-http` mode (locally or deployed), connect via URL instead of spawning a subprocess.

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "levelang": {
      "url": "http://localhost:8463/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "levelang": {
      "url": "http://localhost:8463/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

Omit the `headers` block if `MCP_API_KEYS` is not set on the server (auth disabled).

## Development

### Setup

```bash
uv sync
git config core.hooksPath .githooks
```

This enables pre-commit (auto-fix lint + format) and pre-push (lint + format check + tests) hooks.

### Running Tests

```bash
uv run pytest tests/ -v
```

### MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) provides a web UI for browsing and invoking tools and resources:

```bash
npx @modelcontextprotocol/inspector uv run --directory /path/to/levelang-mcp python -m levelang_mcp
```

## Project Structure

```
src/levelang_mcp/
├── __main__.py       # Entrypoint (python -m levelang_mcp)
├── server.py         # MCP tools and resources
├── auth.py           # API-key auth middleware for HTTP transport
├── client.py         # Async HTTP client for the Levelang API
├── config.py         # Environment variable loading
└── formatting.py     # API response → human-readable text

tests/
├── test_auth.py      # Auth middleware and config tests
├── test_client.py    # HTTP client tests (mocked)
├── test_formatting.py
└── test_tools.py     # Tool integration tests (mocked)
```

## Architecture

```
MCP Client              levelang-mcp              Levelang Backend
(Claude, Cursor,   ◄── MCP/stdio ──►   (this)   ─── HTTP ──►   (FastAPI)
 Claude Code)                                     POST /translate
                                                  GET /languages/details
                                                  GET /languages/{code}
```

The MCP server is a stateless wrapper. It translates MCP tool calls into HTTP requests to the Levelang backend and formats responses as human-readable text for the LLM. It does not share code, database connections, or deployment with the backend.

## License

MIT
