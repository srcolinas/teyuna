ARG UV_VERSION=0.11.26
ARG PYTHON_VERSION=3.14.6
# uv images tag Python as major.minor only (e.g. python3.14), not patch (python3.14.6)
ARG PYTHON_MINOR=3.14

# ============================================
# Stage: Builder — install Python deps with uv
# ============================================
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_MINOR}-trixie AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependency manifests first for layer caching.
COPY teyuna-sdk/pyproject.toml teyuna-sdk/uv.lock teyuna-sdk/README.md teyuna-sdk/LICENSE ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev --no-editable

COPY teyuna-sdk/src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

# ============================================
# Stage: Runtime — minimal production image
# ============================================
FROM python:${PYTHON_VERSION}-slim-trixie

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH" \
    TEYUNA_LOG_ROOT=/var/log/teyuna

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/sh appuser && \
    mkdir -p /var/log/teyuna && \
    chown appuser:appuser /var/log/teyuna

COPY --from=builder --chown=appuser:appuser /app /app
COPY --chown=appuser:appuser teyuna-sdk/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT []

USER appuser

CMD ["/app/docker-entrypoint.sh"]
