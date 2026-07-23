# Teyuna Frontend

Observer UI for Teyuna: The Lost City.

## Prerequisites

- Node.js 18+ and [pnpm](https://pnpm.io/) 9+ (Corepack: `corepack enable`)
- A running Teyuna backend
- `VITE_API_URL` set to the browser-reachable backend base URL (required; no default)

Copy the example env file before the first local run:

```bash
cp .env.example .env
# edit VITE_API_URL if your backend is not at http://localhost:8000
```

## Quick Start

From the repository root (preferred):

```bash
make setup
cd apps/frontend && pnpm run dev
```

Or only the frontend package:

```bash
cd apps/frontend
make setup
pnpm run dev
```

Open: `http://localhost:5173/?gameId=YOUR_GAME_ID`

## Validation

Same workflow as the other packages (also wired into the root Makefile / pre-commit):

```bash
make format   # prettier + eslint --fix
make lint     # prettier/eslint/tsc checks
make test     # vitest
make check    # lint + test
```

## Features

- 19-hex hexagonal game board
- Color-coded terrain types
- Player information panel
- Real-time state updates (2-second polling)
- Game phase and active-agent display
- Responsive design

## API Integration

The observer reads public game state and server-sent events from `VITE_API_URL`.
It does not submit game actions on behalf of agents. Exact hands can optionally
be unlocked with the corresponding agent's Bearer token through the authenticated
`/hand` endpoint.

## Project Structure

```
apps/frontend/
├── src/
│   ├── App.tsx                # Main app component
│   ├── api.ts                 # API client (requires VITE_API_URL)
│   ├── types.ts               # TypeScript definitions
│   ├── hexUtils.ts            # Hex coordinate utilities
│   ├── components/
│   │   ├── GameBoard.tsx      # Board rendering
│   │   ├── PlayerPanel.tsx    # Player info
│   │   └── GamePhasePanel.tsx # Game controls
│   ├── main.tsx               # Entry point
│   └── index.css              # Tailwind CSS
├── .env.example               # Documents VITE_API_URL
├── Makefile
├── package.json
└── vite.config.ts
```

## Building for Production

```bash
pnpm run build
```

`VITE_API_URL` must be set in the environment (or `.env`) at build time. Output
goes to `dist/`.

## Troubleshooting

**Missing `VITE_API_URL`** → Copy `.env.example` to `.env` (or export the variable)
**"Failed to load game"** → Check backend is running and game ID is correct
**"Network Error"** → Ensure `VITE_API_URL` points at a reachable backend
**Stale data** → Frontend auto-updates every 2 seconds, or press F5
