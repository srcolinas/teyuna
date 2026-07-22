# 🏔️ Teyuna Frontend

The web-based frontend for the Teyuna: The Lost City strategy board game.

## Prerequisites

- Node.js 18+ and npm 9+
- Backend running at http://localhost:8000

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173/?gameId=YOUR_GAME_ID`

## Features

✅ 19-hex hexagonal game board
✅ Color-coded terrain types
✅ Player information panel
✅ Real-time state updates (2-second polling)
✅ Game phase and turn management
✅ Responsive design

## API Integration

All backend endpoints are implemented and ready in `src/api.ts`:
- Game state fetching
- Dice rolling
- Building placement
- Trading system
- Wisdom card management
- Conquistador movement

## Project Structure

```
frontend/
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
├── package.json
└── vite.config.ts
```

## Building for Production

```bash
npm run build
```

Output goes to `dist/` directory.

## Customization

Edit `src/types.ts` to change:
- Hex colors (`HEX_TYPE_COLORS`)
- Player colors in `App.tsx`

## Troubleshooting

**"Failed to load game"** → Check backend is running and game ID is correct
**"Network Error"** → Ensure backend at http://localhost:8000
**Stale data** → Frontend auto-updates every 2 seconds, or press F5

See [SETUP_GUIDE.md](../SETUP_GUIDE.md) for complete setup instructions.
