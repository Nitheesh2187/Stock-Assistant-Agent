# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Install Python dependencies ────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Install git for GitHub-hosted packages
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install stock MCP server from GitHub
RUN uv pip install --no-cache git+https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git

# ── Stage 3: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

# Install Node.js (required for firecrawl-mcp via npx)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python venv from build stage
COPY --from=uv /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy backend source
COPY backend/ /app/backend/

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
