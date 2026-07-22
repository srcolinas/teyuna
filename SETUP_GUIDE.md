# Teyuna development setup

The repository is a monorepo:

```text
apps/frontend/          React observer UI
packages/backend/       FastAPI game server
packages/sdk-python/    Python SDK and simulation agents
packages/shared-core/   Shared rules and API models
```

## Prerequisites

- Docker with Compose
- Python 3.14 and `uv`
- Node.js 18+ and npm

## Run a complete simulation

Start the backend from the repository root:

```bash
docker compose up -d backend
```

Start three legal stochastic agents in another terminal:

```bash
uv run teyuna-simulate stochastic:Alice stochastic:Bob stochastic:Charlie
```

The command creates a game, joins the agents, and prints its game ID.

Start the frontend in a third terminal:

```bash
cd apps/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173/?gameId=YOUR_GAME_ID
```

The UI polls public game state and listens to `GET /games/{game_id}/events`.
It does not control the agents. Exact resources and unplayed wisdom cards are
available only through the authenticated `GET /games/{game_id}/hand` endpoint.

## Validate the repository

From the root:

```bash
make check
```

Build the frontend separately:

```bash
cd apps/frontend
npm run build
```

## Useful endpoints

- `POST /games` — create a game
- `POST /games/{game_id}/players` — join a player
- `GET /games/{game_id}` — public game state
- `GET /games/{game_id}/hand` — authenticated player's private hand
- `GET /games/{game_id}/events` — live server-sent game events
- `POST /games/{game_id}/trades` — propose a player trade
- `POST /games/{game_id}/trades/supply` — supply/harbor trade

Interactive API documentation is at `http://localhost:8000/docs` while the
backend is running.
