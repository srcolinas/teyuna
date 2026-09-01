# Getting started

This guide walks you from a fresh clone to a running game with sample AI agents.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Task](https://taskfile.dev) (`brew install go-task` or see the [install docs](https://taskfile.dev/installation/))
- Node.js 18+ and [pnpm](https://pnpm.io/) (Corepack: `corepack enable`) to build the observer UI

## 1. Start the game server

From the repository root:

```bash
task setup
task run
```

That installs the workspace, builds the observer into `apps/frontend/dist`,
and runs uvicorn with `TEYUNA_STATIC_DIR` pointing at that directory (Ctrl+C stops it).
Default:

- Server: `http://127.0.0.1:8000` (`BACKEND_PORT` overrides the port, e.g. `task run BACKEND_PORT=9000`)

The observer UI is served from the same origin as the API.

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
task setup
```

That installs `teyuna-sdk`, `teyuna-core`, and the backend package into the workspace venv.

## 3. Run a simulation

Easiest path — build the observer, start uvicorn, wait for health, create a game,
then join with three trader agents. `join` prints `host`, `game_id`, and each
player's Bearer token (useful for the observer):

```bash
task simulate
```

It prints a `Watch:` URL with the new game id. The server keeps running after the
agents finish so you can inspect the final board; stop it with Ctrl+C.

Games are stored in memory, so restarting the server discards them. A `gameId`
from an earlier run returns 404 and the observer shows "Simulation unavailable" —
use the id printed by the current run.

With the server already up, create a game (prints only the game id), then join:

```bash
GAME_ID=$(teyuna-simulate create --host http://127.0.0.1:8000)
teyuna-simulate join "$GAME_ID" --host http://127.0.0.1:8000 \
  builder:alice sleepy:bob skipper:carol
```

Player specs are `agent` or `agent:nickname` (1–4). Create takes optional
`--num-players` (`3` or `4`, default `3`).

Available built-in agents: `builder`, `skipper`, `sleepy`, `trader`.

Open the observer with the printed game id:
`http://127.0.0.1:8000/?gameId=<uuid>`.

## 4. Logs

`task simulate` writes agent and game-loop logs under `<repo>/logs/<YYYY-MM-DD-HH-MM>`. Running `teyuna-simulate join` yourself uses `logs/<YYYY-MM-DD-HH-MM>` relative to the current working directory unless you pass `--logdir PATH`.
