# levelang-mcp

[![CI](https://github.com/beverage/levelang-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/beverage/levelang-mcp/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP SDK](https://img.shields.io/badge/MCP%20SDK-1.26+-purple.svg)](https://modelcontextprotocol.io/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet.svg)](https://docs.astral.sh/uv/)

The dev-workflow [MCP](https://modelcontextprotocol.io/) server for Levelang. Claude Code spawns it over stdio (through the constellation's `.mcp.json`) for prompt tuning, quality work and agentic translation tasks. It is a stateless wrapper around the `levelang-backend` HTTP API.

End users do not use this server. The product surface for Claude Desktop, Claude.ai and ChatGPT is [`levelang-mcp-app`](https://github.com/beverage/levelang-mcp-app), which renders interactive views (DEC-021).

---

## What it exposes

- **Tools**
  - `translate`: one translation at a level, with optional `source_language`, `mood`, `mode` and `model`.
  - `translate_compare`: the same text at several levels (all of them unless `levels` is given).
  - `list_languages`: the languages with their levels, moods and modes.
- **Prompt**: `compare_levels`, which asks for a `translate_compare` run and a short analysis of what changes between levels.
- **Resources**: `levelang://languages` and `levelang://languages/{code}`.

Levels are beginner, intermediate, advanced and fluent. Mandarin and Cantonese use three: beginner, advanced, fluent. Moods are casual and formal, plus honorific for Japanese. Modes are written and spoken, and some languages are spoken only. `list_languages` gives the live set.

Omitting `source_language` lets the backend default it, which also allows a same-language rewrite at another level.

## Local stdio setup

This needs Python 3.12+, [uv](https://docs.astral.sh/uv/) and a running backend (see the `levelang-backend` README).

```bash
uv sync
git config core.hooksPath .githooks   # pre-commit: lint + format fix; pre-push: lint, format check, tests
```

The constellation's `.mcp.json` registers it like this:

```json
{
  "mcpServers": {
    "levelang": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/levelang-mcp", "python", "-m", "levelang_mcp"],
      "env": {
        "LEVELANG_API_BASE_URL": "http://localhost:8000/api/v1",
        "LEVELANG_API_KEY": "sk_local_dev",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

`sk_local_dev` comes from `llc db seed-keys` in `levelang-backend`. For staging or production, use a plain (non-admin) service key.

## Configuration

All configuration is through environment variables, or a `.env` file (see `.env.example`).

| Variable | Default | Description |
|----------|---------|-------------|
| `LEVELANG_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend URL |
| `LEVELANG_API_KEY` | none | Service key (`sk_*`) for backend auth |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP (`0.0.0.0` in a container) |
| `MCP_PORT` | `8463` | Port for HTTP |
| `MCP_API_KEYS` | none | Comma-separated client keys for HTTP. Unset means no client auth. |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_FORMAT` | `auto` | `auto`, `json` or `text`. `auto` is JSON for HTTP and text for stdio. |

## HTTP deployment

For remote dev use, the server also runs with `MCP_TRANSPORT=streamable-http`. Clients send `Authorization: Bearer <key>` with a key from `MCP_API_KEYS`, and `/health` is open.

It deploys to Fly.io as `levelang-mcp-staging` in `cdg`, on port 8080 (`fly.toml`). CI (`.github/workflows/ci.yml`) runs lint, format check, mypy and tests on pushes and pull requests to `main`, and deploys on push to `main`.

## Development

```bash
uv run pytest tests/ -v
uv run ruff check src/ tests/
uv run mypy src/
```

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) gives a web UI for calling the tools and resources:

```bash
npx @modelcontextprotocol/inspector uv run --directory /path/to/levelang-mcp python -m levelang_mcp
```

## Project structure

```
src/levelang_mcp/
├── __main__.py       # Entrypoint (python -m levelang_mcp), stdio or HTTP
├── server.py         # MCP tools, resources and prompt
├── auth.py           # API-key middleware and /health for HTTP
├── client.py         # Async HTTP client for the backend
├── config.py         # Environment variable loading
├── formatting.py     # Backend JSON to readable text
└── logging_config.py # Logging setup

tests/                # auth, client, formatting, lifecycle, logging, tools
```

## Architecture

```
Claude Code          levelang-mcp          levelang-backend
(.mcp.json)   ◄── stdio or HTTP ──►  (this)  ── HTTP ──►  POST /translate
                                                         GET  /languages/details
                                                         GET  /languages/{code}
```

The server keeps no state and shares no code or database with the backend. See [CLAUDE.md](CLAUDE.md) for coupling points.

## License

MIT
