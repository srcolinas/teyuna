# API reference

The authoritative HTTP schemas live in the running server's OpenAPI UI:

| URL | Purpose |
| --- | --- |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | Raw OpenAPI document |

The Python SDK mirrors these routes 1:1 — prefer [sdk-reference.md](sdk-reference.md) if you are writing an agent in Python.

Default base URL: `http://127.0.0.1:8000`.

---

## Authentication

- Join a game with `POST /games/{game_id}/players` and a JSON body `{"nickname": "..."}`.
- The response sets an HTTP-only cookie: `session-token`.
- Send that cookie on every authenticated request (hand, builds, trades, turn advance, chat WebSocket).
- Identity is the nickname chosen at join time. There are no API keys or Bearer tokens.

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
POST .../initial-placements (×2N)   → second placement → dice roll
main loop:
  POST .../turn-order               → roll
  (optional discard / conquistator / wisdom sub-phases)
  trade & build endpoints
  POST .../turn-order               → end turn → next player
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
| Turn | `POST .../turn-order` |
| Conquistator | `POST .../conquistator` |
| Discard | `POST .../discard` |
| Wisdom | `POST .../wisdom-cards`, `.../wisdom-cards/buy`, `.../mamo`, `.../blessing`, `.../pathfinder` |
| Trades | `POST .../trades`, `.../trades/{id}/accept`, `.../trades/supply` |
| Setup | `POST .../initial-placements` |
| Build | `POST .../settlements`, `POST .../paths` |
| Events | `GET .../events` (SSE) |
| Chat | `WS .../chat` (text chat only; not used for game actions) |

Common errors: `400` illegal action / bad request, `401` missing session, `404` missing game/player, `501` no handler for phase.

---

## Server-sent events

`GET /games/{game_id}/events` streams action results after the game leaves the lobby.

- Initial comment: `:connected`
- Each event: JSON `ActionExecutionResult` (previous/next phase, action payload, optional error)
- The SDK exposes this as `GameClient.stream_events(game_id)`

---

## Related docs

- [Getting started](getting-started.md)
- [Writing agents](writing-agents.md)
- [SDK reference](sdk-reference.md)
- Rulebook: [`rulebook.md`](../rulebook.md)
