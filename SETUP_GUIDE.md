# 🎮 Complete Setup Guide - Teyuna Frontend & Backend

Detailed step-by-step instructions to get Teyuna running from scratch.

## Prerequisites

### Check Your System

```bash
python --version  # Should be 3.10 or higher
node --version    # Should be v18 or higher
npm --version     # Should be 9 or higher
```

If you need to install:
- Python: https://www.python.org/
- Node.js: https://nodejs.org/

## Step 1: Start the Backend

Open **Terminal 1**:

```bash
cd /Users/elizabethgranda/Documents/teyuna/backend
```

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn
```

Start the server:

```bash
python -m uvicorn src.main:create_app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Keep this terminal open - backend must stay running**

Verify it's working:
```bash
curl http://localhost:8000/
```

Or visit: http://localhost:8000/docs (Swagger API documentation)

---

## Step 2: Create a Game

Open **Terminal 2**:

```bash
# Create a 3-player game
curl -X POST http://localhost:8000/proposed-games \
  -H "Content-Type: application/json" \
  -d '{"players_count": 3}'
```

Response (save the `id`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "player_count": 3
}
```

Use this ID as `{GAME_ID}` below.

---

## Step 3: Players Join the Game

Each player must join. Run these commands (replacing `{GAME_ID}`):

### Player 1 (Alice):
```bash
curl -X POST http://localhost:8000/proposed-games/550e8400-e29b-41d4-a716-446655440000/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Alice"}'
```

Response (save `active_game_id`):
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "player": "Alice",
  "active_game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Player 2 (Bob):
```bash
curl -X POST http://localhost:8000/proposed-games/550e8400-e29b-41d4-a716-446655440000/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Bob"}'
```

### Player 3 (Charlie):
```bash
curl -X POST http://localhost:8000/proposed-games/550e8400-e29b-41d4-a716-446655440000/players \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Charlie"}'
```

✅ **Save the `active_game_id` - you'll need this for the frontend!**

---

## Step 4: Install Frontend Dependencies

Open **Terminal 3**:

```bash
cd /Users/elizabethgranda/Documents/teyuna/frontend
npm install
```

This installs React, TypeScript, Vite, Tailwind CSS, and Axios. Takes 2-5 minutes.

---

## Step 5: Start the Frontend Dev Server

In Terminal 3:

```bash
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ **Frontend is now running**

---

## Step 6: Open the Game in Your Browser

Replace `a1b2c3d4-e5f6-7890-abcd-ef1234567890` with your `active_game_id`:

```
http://localhost:5173/?gameId=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**You should now see:**
- ✅ Hexagonal game board with 19 hexes
- ✅ Color-coded terrain types
- ✅ Dice numbers on hexes
- ✅ Player information panel
- ✅ Game phase and action buttons

---

## Testing the Game

### Test 1: Check Board Display
- [ ] See 19 hexagons arranged in hexagonal pattern
- [ ] Each hex has a color (mountains=brown, quarries=gray, etc.)
- [ ] Each hex shows a number (2-12) in the center
- [ ] Hex type label appears above each hex

### Test 2: Check Player Panel
- [ ] Player names visible on right side
- [ ] One player highlighted in yellow (active player)
- [ ] Resources count showing
- [ ] Wisdom cards count showing
- [ ] Available buildings showing

### Test 3: Check Game Controls
- [ ] Current phase displayed
- [ ] Active player name shown
- [ ] Only active player's buttons are enabled
- [ ] Other player's buttons are greyed out

### Test 4: Roll Dice
- [ ] Click "🎲 Roll Dice" (as active player)
- [ ] Game state should update
- [ ] Check frontend updates automatically (within 2 seconds)

### Test 5: End Turn
- [ ] Click "➡️ End Turn" (as active player)
- [ ] Different player should be highlighted
- [ ] That player's buttons should become enabled

---

## Common Issues & Solutions

### "Failed to load game: Network Error"
**Solution:**
1. Make sure backend is running (Terminal 1)
2. Verify game ID is correct (should be `active_game_id`, not `game_id`)
3. Check backend logs for errors

### Frontend shows old/stale data
**Solution:**
1. Frontend polls every 2 seconds - wait a moment
2. Press F5 to force refresh
3. Check browser console (F12) for errors

### Backend won't start
**Solution:**
1. Check Python version: `python --version`
2. Ensure packages installed: `pip install fastapi uvicorn`
3. Try different port: `--port 8001`
4. Check firewall isn't blocking port 8000

### npm install fails
**Solution:**
1. Check Node version: `node --version`
2. Clear npm cache: `npm cache clean --force`
3. Delete node_modules: `rm -rf node_modules`
4. Try again: `npm install`

### Buttons are greyed out
**Solution:**
1. This is correct behavior!
2. Only the active player can use buttons
3. Active player has yellow border on right panel
4. Wait for your turn (button will activate)

---

## All Endpoints Reference

### Game State
- `GET /active-games/{gameId}` - Get full game state
- `GET /active-games/{gameId}/map` - Get map/hexes
- `GET /active-games/{gameId}/turn-order` - Get turn order

### Turn Management
- `POST /active-games/{gameId}/turn-order` - Advance turn/phase

### Dice & Actions
- `POST /active-games/{gameId}/dice` - Roll dice

### Building
- `POST /active-games/{gameId}/settlements` - Build settlement
- `POST /active-games/{gameId}/paths` - Build stone path

### Wisdom Cards
- `POST /active-games/{gameId}/wisdom-cards` - Play card
- `POST /active-games/{gameId}/wisdom-cards/buy` - Buy card

### Trading
- `POST /active-games/{gameId}/trades` - Propose trade
- `POST /active-games/{gameId}/trades/{proposalId}/accept` - Accept trade
- `POST /active-games/{gameId}/trades/supply` - Trade with bank

### Conquistador
- `GET /active-games/{gameId}/conquistator` - Get location
- `POST /active-games/{gameId}/conquistator` - Move

---

## Verify Everything Works

Check all three servers are running:

```bash
# Terminal 1: Backend
curl http://localhost:8000/docs  # Should see Swagger UI

# Terminal 2: Should have game ID and active_game_id saved

# Terminal 3: Frontend
open http://localhost:5173/?gameId=YOUR_GAME_ID
```

If you see the game board with hexagons in your browser, **you're ready to play!** 🎉

---

## Next Steps

1. **Play the game** - Click buttons, watch updates
2. **Customize colors** - Edit `frontend/src/types.ts`
3. **Add features** - Expand frontend components
4. **Deploy** - `npm run build` creates production build

---

## Files Structure

```
teyuna/
├── backend/          # Backend API (Python/FastAPI)
├── frontend/         # Frontend (React/TypeScript)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   ├── hexUtils.ts
│   │   └── components/
│   ├── package.json
│   └── vite.config.ts
├── QUICK_START.md    # This quick version
├── SETUP_GUIDE.md    # This complete version
└── rulebook.md       # Game rules
```

---

For faster setup, see: [QUICK_START.md](QUICK_START.md)
For frontend usage, see: [frontend/README.md](frontend/README.md)
