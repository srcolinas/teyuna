# 🚀 Quick Start Guide - Teyuna Frontend

Get the game running in 5 minutes!

## Prerequisites
- Python 3.10+ 
- Node.js 18+
- Terminal with bash/zsh

## Terminal 1: Start Backend

```bash
cd /Users/elizabethgranda/Documents/teyuna/backend
pip install fastapi uvicorn  # if needed
python -m uvicorn src.main:create_app --port 8000 --reload
```

✅ You should see: `Uvicorn running on http://0.0.0.0:8000`

## Terminal 2: Create Game & Players

```bash
# Create a 3-player game
curl -X POST http://localhost:8000/proposed-games \
  -H "Content-Type: application/json" \
  -d '{"players_count": 3}'

# Get the game ID from response, then add players:

curl -X POST http://localhost:8000/proposed-games/{GAME_ID}/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Alice"}'

curl -X POST http://localhost:8000/proposed-games/{GAME_ID}/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Bob"}'

curl -X POST http://localhost:8000/proposed-games/{GAME_ID}/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Charlie"}'
```

Save the `active_game_id` from responses!

## Terminal 3: Start Frontend

```bash
cd /Users/elizabethgranda/Documents/teyuna/frontend
npm install
npm run dev
```

✅ You should see: `Local: http://localhost:5173/`

## Step 4: Open in Browser

```
http://localhost:5173/?gameId=YOUR_ACTIVE_GAME_ID
```

**Done!** 🎉 Game board should appear with hexagons, player info, and controls.

---

## Testing

- **Roll Dice**: Click 🎲 button (as active player)
- **End Turn**: Click ➡️ button to pass to next player
- **Watch Updates**: Frontend auto-updates every 2 seconds

---

For detailed setup: [SETUP_GUIDE.md](SETUP_GUIDE.md)
