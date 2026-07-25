# Getting started

This guide walks you from a fresh clone to a running game with sample AI agents.

## Requirements

- [Docker](https://docs.docker.com/get-docker/) (or Podman) for the recommended server path
- Python 3.14+ if you install the SDK locally
- [uv](https://docs.astral.sh/uv/) if you develop inside this monorepo
- Node.js 18+ and [pnpm](https://pnpm.io/) (Corepack: `corepack enable`) for the frontend

## 1. Start the game server

From the repository root:

```bash
make run
```

That builds and starts the `backend` and `frontend` Compose services in the
foreground (so published URLs stay visible; Ctrl+C stops them). Defaults:

- Backend: `http://127.0.0.1:8000` (`BACKEND_PORT` overrides the host port)
- Frontend: `http://127.0.0.1:5173` (`FRONTEND_PORT` overrides the host port)
- Frontend build arg `VITE_API_URL` defaults to `http://localhost:8000`

Backend only:

```bash
docker compose up -d backend
```

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

That installs `teyuna-sdk`, `teyuna-core`, and the backend package into the workspace venv.

## 3. Run a simulation

Easiest path — start Compose detached, wait for backend health, create a game,
then join with three trader agents. `join` prints `host`, `game_id`, and each
player's Bearer token (useful for the frontend observer):

```bash
make simulate
```

With the server already up, create a game (prints only the game id), then join:

```bash
GAME_ID=$(teyuna-simulate create --host http://127.0.0.1:8000)
teyuna-simulate join "$GAME_ID" --host http://127.0.0.1:8000 \
  builder:alice sleepy:bob skipper:carol
```

Player specs are `agent` or `agent:nickname` (1–4). Create takes optional
`--num-players` (`3` or `4`, default `3`).

Available built-in agents: `builder`, `skipper`, `sleepy`, `trader`.

Open the frontend observer with the printed game id:
`http://127.0.0.1:5173/?gameId=<uuid>`.

## 4. Logs

`teyuna-simulate join` writes agent and game-loop logs under `logs/<YYYY-MM-DD-HH-MM>` by default. Pass `--logdir PATH` to write into a specific directory instead.
