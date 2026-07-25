ARG UV_VERSION=0.11.26
ARG PYTHON_VERSION=3.12.13
# uv images tag Python as major.minor only (e.g. python3.12), not patch (python3.12.13)
ARG PYTHON_MINOR=3.12

# ============================================
# Stage: Builder — install Python deps with uv
# ============================================
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_MINOR}-trixie AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Workspace manifests first for layer caching.
COPY pyproject.toml uv.lock ./
COPY packages/backend/pyproject.toml packages/backend/README.md packages/backend/
COPY packages/sdk-python/pyproject.toml packages/sdk-python/
COPY packages/teyuna-core/pyproject.toml packages/teyuna-core/README.md packages/teyuna-core/
# Path dependency must be buildable during the first sync.
COPY packages/teyuna-core/src/ ./packages/teyuna-core/src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package backend --no-install-project --no-dev --no-editable

# Runtime layout: src/ at /app/src for uvicorn src.main:create_app
COPY packages/backend/src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --package backend --no-dev --no-editable

# ============================================
# Stage: Runtime — minimal production image
# ============================================
FROM python:${PYTHON_VERSION}-slim-trixie

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH"

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/sh appuser

COPY --from=builder --chown=appuser:appuser /app /app

ENTRYPOINT []

USER appuser

CMD ["uvicorn", "src.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
