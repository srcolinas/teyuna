# Teyuna Frontend

Observer UI for Teyuna: The Lost City.

In production the backend serves this app from the same origin as the API.
Local Vite dev still runs on port 5173 and proxies `/games` and `/health` to
`http://127.0.0.1:8000`.

## Prerequisites

- Node.js 18+ and [pnpm](https://pnpm.io/) 9+ (Corepack: `corepack enable`)
- A running Teyuna backend (for live data)

## Quick Start

From the repository root (preferred):

```bash
task setup
cd apps/frontend && pnpm run dev
```

Or only the frontend package:

```bash
task frontend:setup
cd apps/frontend
pnpm run dev
```

Open: `http://localhost:5173/?gameId=YOUR_GAME_ID`

Packaged server (API + built observer): `http://127.0.0.1:8000/?gameId=YOUR_GAME_ID`

## Validation

Same workflow as the other packages (also wired into the root Taskfile / pre-commit):

```bash
task frontend:format   # prettier + eslint --fix
task frontend:lint     # prettier/eslint/tsc checks
task frontend:test     # vitest
task frontend:check    # lint + test
```

## Features

- 19-hex hexagonal game board
- Color-coded terrain types
- Player information panel
- Real-time state updates (2-second polling)
- Game phase and active-agent display
- Responsive design

## API Integration

The observer calls same-origin `/games` (and, in Vite, the proxy to the backend).
It does not submit game actions on behalf of agents. Exact hands can optionally
be unlocked with the corresponding agent's Bearer token through the authenticated
`/hand` endpoint.

## Project Structure

```
apps/frontend/
├── src/
│   ├── App.tsx                # Main app component
│   ├── api.ts                 # API client
│   ├── types.ts               # TypeScript definitions
│   ├── hexUtils.ts            # Hex coordinate utilities
│   ├── components/
│   │   ├── GameBoard.tsx      # Board rendering
│   │   ├── PlayerPanel.tsx    # Player info
│   │   └── GamePhasePanel.tsx # Game controls
│   ├── main.tsx               # Entry point
│   └── index.css              # Tailwind CSS
├── Taskfile.yaml
├── package.json
└── vite.config.ts
```

## Building for Production

```bash
pnpm run build
```

Output goes to `apps/frontend/dist/` so FastAPI can serve it (`TEYUNA_STATIC_DIR`).

## Troubleshooting

**"Failed to load game"** → Check the backend is running and the game ID is correct
**"Network Error"** → Start the backend on port 8000 (Vite proxies `/games` there)
**Stale data** → Frontend auto-updates every 2 seconds, or press F5
