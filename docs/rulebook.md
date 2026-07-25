# Game Rules

## Objective

Be the first player to reach **10 Victory Points**.

## Setup

1. When the lobby fills, players enter **first placement** in a random turn order.
2. Going **clockwise**, each player places one **Terrace** and one adjacent **Path**.
3. Then **second placement** runs **counter-clockwise**: each player places another Terrace and Path.
4. After your second Terrace, you receive one resource for each producing hex adjacent to that Terrace.
5. The first player in turn order begins the first **dice roll**.

For API phase names and when actions are legal, see [agents.md](agents.md).

## Turn Structure

Each turn uses these server phases:

1. **dice roll** — Active player rolls. On a non-7, matching hexes produce resources automatically for all players.
2. On a **7**:
   - Players with **more than 7** resource cards enter **discard resources** and must discard half (rounded down).
   - Then the active player enters **move conquistator**, moves the Conquistator, and may steal one resource from a player adjacent to the new hex. The blocked hex produces nothing while occupied.
3. **trade and build** — Active player may build, buy wisdom cards, trade, and play wisdom cards, then ends the turn (`advance`) so the next player rolls.

Wisdom cards played from **dice roll** or **trade and build** briefly enter resolve phases such as `dice play warrior` or `trade and build play mamo`.

## Victory Points

- Each **Terrace** = 1 VP
- Each **Great Terrace** = 2 VP
- Longest Path (5+ continuous paths) = 2 VP
- Largest Army (3+ warriors played) = 2 VP
- **legacy of the elders** wisdom cards = 1 VP each

## Resources

| Resource | Source |
|----------|--------|
| gold | mountains |
| stone | quarries |
| cotton | highlands |
| maize | valleys |
| wood | jungle |

## Buildings

| Building | Cost | Victory Points |
|----------|------|----------------|
| Path | 1 stone + 1 wood | 0 |
| Terrace | 1 stone + 1 wood + 1 cotton + 1 maize | 1 |
| Great Terrace | 3 gold + 2 maize | 2 |

Wisdom card from the deck: 1 gold + 1 cotton + 1 maize.

## Wisdom Cards

Wire / API names (exact strings):

- **warrior** — Move the Conquistator (and steal as with a 7)
- **blessing of aluna** — Take 2 resources from the bank
- **wisdom of mamo** — Monopoly: take all cards of one resource from every opponent
- **pathfinder** — Build up to 2 free paths
- **legacy of the elders** — 1 Victory Point
