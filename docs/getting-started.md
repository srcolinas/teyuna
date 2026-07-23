# Getting started

This guide walks you from a fresh clone to a running game with sample AI agents.

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (or Podman) for the recommended server path
- Python 3.14+ if you install the SDK locally
- [uv](https://docs.astral.sh/uv/) if you develop inside this monorepo

## 1. Start the game server

From the repository root:

```bash
docker compose up -d backend
```

Or build and start both the server and the sample players service:

```bash
make run
# optional: make run NUM_PLAYERS=4
```

The backend listens on `http://127.0.0.1:8000` by default (`BACKEND_PORT` overrides the host port).

### Verify the server

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok"}
```

Interactive OpenAPI (Swagger) is available at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc
- http://127.0.0.1:8000/openapi.json

## 2. Install the Python SDK

Against a published package:

```bash
pip install teyuna-sdk
# or: uv add teyuna-sdk
```

From this monorepo (editable workspace):

```bash
make setup
```

That installs `teyuna-sdk`, `teyuna-shared-core`, and the backend package into the workspace venv.

## 3. Run a simulation

With the server up, run the built-in agents:

```bash
teyuna-simulate --host http://127.0.0.1:8000
```

Defaults to three agents: `builder`, `sleepy`, and `skipper`.

Custom mix (form is `agent` or `agent:nickname`):

```bash
teyuna-simulate --host http://127.0.0.1:8000 \
  builder:alice sleepy:bob skipper:carol
```

Join an existing game instead of creating one:

```bash
teyuna-simulate --host http://127.0.0.1:8000 --game-id <uuid> \
  builder:alice sleepy:bob skipper:carol
```

Available built-in agents: `builder`, `skipper`, `sleepy`, `stochastic`.

### Docker players service

`make run` also starts the `players` compose service, which runs `teyuna-simulate` against `http://backend:8000` and writes logs under `./logs`.

## 4. Logs

When using the Docker `players` service, per-run logs appear under:

```text
logs/<timestamp>/
  game_loop.log
  builder.log
  sleepy.log
  skipper.log
  ...
```

For local `teyuna-simulate`, set `TEYUNA_LOG_ROOT` (or `TEYUNA_LOG_DIR`) if you want the same file logging layout.

## Next steps

- Write your own agent: [writing-agents.md](writing-agents.md)
- Browse SDK methods: [sdk-reference.md](sdk-reference.md)
- HTTP/SSE overview: [api-reference.md](api-reference.md)
- Full game rules: [rulebook.md](../rulebook.md)
