# API reference

The authoritative HTTP schemas live in the running server's OpenAPI UI:

| URL | Purpose |
| --- | --- |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | Raw OpenAPI document |

The Python SDK mirrors these routes — prefer [sdk-reference.md](sdk-reference.md) if you are writing an agent in Python. Mutations go through `AuthenticatedPlayerClient.submit_action` (or convenience wrappers that call it).

Default base URL: `http://127.0.0.1:8000`.

---

## Authentication

- Join a game with `POST /games/{game_id}/players` and a JSON body `{"nickname": "..."}`.
- The response sets an HTTP-only cookie: `session-token`.
- Send that cookie on every authenticated request (hand, actions, chat WebSocket).
- Identity is the nickname chosen at join time. There are no API keys or Bearer tokens.
- For `POST .../actions`, the server sets `by` from the session and forces `due_to_timeout=false` (client values are ignored).

Public reads (`GET /games/{id}`, map, players, events) do not require auth.

---

## Global routes

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Liveness: `{"status":"ok"}` |

---

## Game lifecycle (overview)

```text
POST /games                         → lobby
POST /games/{id}/players (×N)       → when full: first placement
POST .../actions (free_placement ×2N) → second placement → dice roll
main loop:
  POST .../actions (advance)        → roll
  (optional discard / conquistator / wisdom actions)
  trade & build actions
  POST .../actions (advance)        → end turn → next player
building / cards may move phase to end game
```

- `GET /games/{id}` returns the full public `Game` snapshot anytime.
- `turn_order[0]` is the active player; empty `turn_order` means lobby.
- `phase` and `phase_deadline` tell you what action is expected and when the server will auto-act.

Private hand data is only on `GET /games/{id}/hand` (auth required). Other clients see aggregates on `Player` (`num_resources`, `num_hidden_wisdom_cards`), not exact cards.

---

## Endpoint groups under `/games`

Exact request/response models: use `/docs`. Grouped list:

| Group | Methods |
| --- | --- |
| Lifecycle | `POST /games`, `POST /games/{id}/players`, `GET /games/{id}` |
| Read state | `GET .../map`, `.../turn-order`, `.../conquistator`, `.../players`, `.../players/{nickname}`, `.../hand`, `.../settlements`, `.../paths` (+ per-coordinate GETs) |
| Actions | `POST .../actions` (discriminated union body; see below) |
| Events | `GET .../events` (SSE) |
| Chat | `WS .../chat` (text chat only; not used for game actions) |

Common errors: `400` illegal action / bad request, `401` missing session, `404` missing game/player, `501` no handler for phase.

---

## Player actions

`POST /games/{game_id}/actions` accepts a JSON body with a `kind` discriminator and returns a matching `ActionExecutionResult` (also discriminated by `kind`).

| Action `kind` | Typical phase | Notes |
| --- | --- | --- |
| `advance` | dice roll / trade and build | Roll dice or end turn |
| `free_placement` | first / second placement | Optional `terrace` / `path` as `{q,r,d}` |
| `discard_resources` | discard resources | `count` map of resource → amount |
| `move_conquistator` | move conquistator / warrior | `q`, `r`, optional `from_player` |
| `play_wisdom_card` | dice roll / trade and build | `card` |
| `buy_wisdom_card` | trade and build | |
| `play_mamo` | mamo sub-phase | `resource` |
| `play_blessed` | blessing sub-phase | `resources` pair |
| `play_pathfinder` | pathfinder sub-phase | `paths` as `{q,r,d}` list |
| `propose_trade` | dice roll / trade and build | `offer`, `request`, `to` |
| `accept_trade` | trade and build | `id` (proposal UUID) |
| `trade_with_supply` | trade and build | `offers`, `requests` |
| `build_settlement` | trade and build | `item`, `coordinate` `{q,r,d}` |
| `build_path` | trade and build | `coordinate` `{q,r,d}` |

Coordinates on the wire use shared `Coordinate` (`q`, `r`, `d`), not the nested `hex_coord` / `direction` read DTOs.

---

## Server-sent events

`GET /games/{game_id}/events` streams action results after the game leaves the lobby.

- Initial comment: `:connected`
- Each event: JSON `ActionExecutionResult` (discriminated `kind`, previous/next phase, nested `action` with its `kind`, optional error)
- The SDK exposes this as typed results via `GameClient.stream_events(game_id)`

---

## Related docs

- [Getting started](getting-started.md)
- [Writing agents](writing-agents.md)
- [SDK reference](sdk-reference.md)
- Rulebook: [`rulebook.md`](../rulebook.md)
