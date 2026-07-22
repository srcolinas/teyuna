# Teyuna observer quick start

## Terminal 1: backend

From the repository root:

```bash
docker compose up -d backend
```

The API is available at `http://localhost:8000`.

## Terminal 2: agent simulation

```bash
uv run teyuna-simulate stochastic:Alice stochastic:Bob stochastic:Charlie
```

Copy the game ID printed by the simulator. The stochastic agents make legal
placements, trades, builds, wisdom-card plays, and other game actions.

## Terminal 3: observer frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Open `http://localhost:5173/?gameId=YOUR_GAME_ID`.

The frontend is an observer: it renders the public board, players, scores, and
live events. A player's exact hand remains private unless that player's session
token is supplied in the optional token field.
