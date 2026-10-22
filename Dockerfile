# Stage 1: Build virtual environment with uv and Python 3.14
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy project configuration and lock file
COPY pyproject.toml uv.lock ./

# Sync dependencies first (without installing the local project package)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable --no-install-project

# Copy README and source files, then do the final project install
COPY README.md ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

# Stage 2: Minimal runtime image with Python 3.14
FROM python:3.14-slim-bookworm AS runner

WORKDIR /app

# Copy virtual environment and source code from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    MCP_TRANSPORT="stdio" \
    HOST="0.0.0.0" \
    PORT="8000"

EXPOSE 8000

# Run the MCP server over stdio or http streamable
ENTRYPOINT ["maitabi", "mcp"]
CMD ["--transport", "stdio"]
