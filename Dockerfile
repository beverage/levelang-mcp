# ---------------------------------------------------------------------------
# Stage 1 – build: install dependencies with uv into a virtual-env
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build

WORKDIR /app

# Enable bytecode compilation for faster startup at runtime.
ENV UV_COMPILE_BYTECODE=1
# Disable installer output for cleaner build logs.
ENV UV_LINK_MODE=copy

# Install dependencies first (layer cache — only re-runs when lock changes).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and metadata needed by hatchling, then install the project.
COPY README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

# ---------------------------------------------------------------------------
# Stage 2 – runtime: slim image with just the venv
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm

WORKDIR /app

# Create a non-root user to run the application.
RUN groupadd --system app && useradd --system --gid app app

# Copy the virtual-env from the build stage.
COPY --from=build /app/.venv /app/.venv

# Ensure the venv's Python is on PATH.
ENV PATH="/app/.venv/bin:$PATH"

USER app

CMD ["python", "-m", "levelang_mcp"]
