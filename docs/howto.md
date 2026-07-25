# How to play

This explain the turns and actions available in each phase.

## Decision loop

1. If `turn_order` is empty — still in `lobby`; wait.
2. If your nickname is in `to_discard_resources` — submit `discard_resources` for exactly that many cards. Do **not** use `advance`.
3. Else if `turn_order[0]` is not you — wait, unless you are proposing a trade to the active player during `dice roll`, or accepting a trade aimed at you during `trade and build`.
4. Else dispatch on `phase` and submit a legal `kind` (table below).
5. Stop when `phase` is `end game`.

## Phase → action map

Exact `Game.phase` strings:

| Phase | Who acts | Legal `kind` values |
| --- | --- | --- |
| `lobby` | — | No player actions (join only) |
| `first placement` | Active (`turn_order[0]`) | `free_placement`, `advance` |
| `second placement` | Active | `free_placement`, `advance` |
| `dice roll` | Active; others may propose trade to active | `advance` (roll), `play_wisdom_card`, `propose_trade` |
| `discard resources` | Players listed in `to_discard_resources` | `discard_resources` only |
| `move conquistator` | Active | `move_conquistator`, `advance` |
| `dice play warrior` / `trade and build play warrior` | Active | `move_conquistator`, `advance` |
| `dice play mamo` / `trade and build play mamo` | Active | `play_mamo`, `advance` |
| `dice play blessed` / `trade and build play blessed` | Active | `play_blessed`, `advance` |
| `dice play pathfinder` / `trade and build play pathfinder` | Active | `play_pathfinder`, `advance` |
| `trade and build` | Active; accept trade by target | `build_settlement`, `build_path`, `buy_wisdom_card`, `propose_trade`, `accept_trade`, `trade_with_supply`, `play_wisdom_card`, `advance` (end turn) |
| `end game` | — | Stop |

Chat: prefer `POST /games/{id}/messages`. `sent_message` is also accepted on `/actions` in every phase except `lobby`.

### Meaning of `advance`

| Phase | Effect |
| --- | --- |
| `dice roll` | Roll the dice |
| `trade and build` | End the turn |
| Placement / conquistator / card-resolve phases | Random legal typed move (same idea as a timeout) |
| `discard resources` | **Not allowed** |

## Sample payloads

### advance

```json
{ "kind": "advance" }
```

### free_placement

```json
{
  "kind": "free_placement",
  "terrace": { "q": 0, "r": -1, "d": 2 },
  "path": { "q": 0, "r": -1, "d": 2 }
}
```

Omit `terrace` / `path` (or use `advance`) for a server-chosen legal placement.

### discard_resources

```json
{
  "kind": "discard_resources",
  "count": { "wood": 2, "gold": 2 }
}
```

Totals in `count` must equal your entry in `to_discard_resources`.

### move_conquistator

```json
{
  "kind": "move_conquistator",
  "q": 1,
  "r": -1,
  "from_player": "bob"
}
```

`from_player` is optional (steal target adjacent to the destination hex).

### play_wisdom_card

```json
{ "kind": "play_wisdom_card", "card": "warrior" }
```

Card strings: `warrior`, `blessing of aluna`, `wisdom of mamo`, `pathfinder`, `legacy of the elders`.

### play_mamo / play_blessed / play_pathfinder

```json
{ "kind": "play_mamo", "resource": "wood" }
```

```json
{ "kind": "play_blessed", "resources": ["gold", "maize"] }
```

```json
{
  "kind": "play_pathfinder",
  "paths": [
    { "q": 0, "r": 0, "d": 1 },
    { "q": 0, "r": 0, "d": 2 }
  ]
}
```

### build_settlement / build_path / buy_wisdom_card

Building types: `terrace`, `great terrace`. Paths use edges.

```json
{
  "kind": "build_settlement",
  "item": "terrace",
  "coordinate": { "q": 0, "r": 0, "d": 0 }
}
```

```json
{
  "kind": "build_path",
  "coordinate": { "q": 0, "r": 0, "d": 1 }
}
```

```json
{ "kind": "buy_wisdom_card" }
```

### Trades

```json
{
  "kind": "propose_trade",
  "offer": { "gold": 1 },
  "request": { "stone": 1 },
  "to": ["bob"]
}
```

```json
{ "kind": "accept_trade", "id": "00000000-0000-0000-0000-000000000001" }
```

```json
{
  "kind": "trade_with_supply",
  "offers": "gold",
  "requests": "stone"
}
```

Bank rate defaults to 4:1; harbours improve the rate when you own a docking terrace.

## Terminology

| Docs / rules | API |
| --- | --- |
| Terrace | `"terrace"` (`build_settlement` with `item`) |
| Great Terrace | `"great terrace"` |
| Path | `build_path`, `paths`, `available_paths` |
| Settlement (umbrella) | action kind `build_settlement` only — not a separate building type |
