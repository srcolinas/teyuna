# Writing agents

Build an AI (or scripted) client that plays Teyuna through the Python SDK.

## Prerequisites

- A running game server ([getting started](getting-started.md))
- `teyuna-sdk` installed

Agents talk to the server over HTTP. Auth is a Bearer token returned in the join response body (`{ game, token }`); the SDK attaches `Authorization: Bearer <token>` for you.

## Agent contract

An agent is an async callable that takes a `PlayerContext` and runs until cancelled:

```python
from teyuna_sdk import entities

async def my_agent(*, context: entities.PlayerContext) -> None:
    ...
```

`PlayerContext` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `nickname` | `str` | Your seat name in the game |
| `game_id` | `uuid.UUID` | Game id |
| `client` | `GameClient` | Authenticated API client for actions |

This matches the `PlayerBuilder` protocol used by `teyuna-simulate` and `GameLoop`.

## Recommended loop

Most sample agents **poll** public state and act when it is their turn:

1. `game = await context.client.get_game()`
2. If `not game.turn_order` you are still in the lobby — wait.
3. If `context.nickname` is in `game.to_discard_resources`, discard (only then). Discard is **not** turn-ordered — do not submit a discard/`PlayerAction` unless you are listed.
4. If `game.turn_order[0] != context.nickname` — sleep and poll again.
5. Otherwise dispatch on `game.phase` and call `submit_action` with the matching action (action and phase types come from `teyuna_core`). Only take actions that are legal for you in that phase; otherwise wait.
6. Optionally call `await context.client.get_hand()` for private resources and cards.

You can also subscribe to SSE via `GameClient.stream_events()` (what `GameLoop.run()` does) and still poll `get_game` / `get_hand` before acting.

## Phase → action cheat sheet

| Phase | Typical `submit_action(...)` |
| --- | --- |
| any constrained phase | `PlayerAction()` — server picks a legal random move (same as a timeout) |
| `first placement` / `second placement` | `FreePlacementAction(terrace=..., path=...)` (or omit both / use `PlayerAction()` to skip); convert with `rules.from_vertex` / `rules.from_edge` |
| `dice roll` | `PlayerAction()` (roll) or `PlayWisdomCardAction(card=...)` |
| `discard resources` | `DiscardResourcesAction(count=...)` using `game.to_discard_resources[nickname]` (or `PlayerAction()` to discard at random) |
| `move conquistator` / `* play warrior` | `MoveConquistatorAction(q=..., r=..., from_player=...)` (or `PlayerAction()`) |
| `* play mamo` | `PlayMamoAction(resource=...)` (or `PlayerAction()`) |
| `* play blessed` | `PlayBlessedAction(resources=(r1, r2))` (or `PlayerAction()`) |
| `* play pathfinder` | `PlayPathfinderAction(paths=...)` (or `PlayerAction()`) |
| `trade and build` | `BuildSettlementAction`, `BuildPathAction`, `BuyWisdomCardAction`, trade actions, then `PlayerAction()` to end the turn |
| `end game` | Stop; the game is over |

Illegal moves return HTTP 400 with a `detail` message. If you wait too long, the server applies a timeout action for the current phase.

## Helper utilities

`teyuna_sdk.rules` provides board helpers used by the sample agents, for example:

- `vertices_available_for_free_placement(game)`
- `edges_for_free_placement(game, terrace)`
- `vertices_available_for_building(game, by=nickname)`
- `edges_available_for_building(game, by=nickname)`
- `can_afford(resources, cost)`
- `pick_discard(resources, required, rng)`

Building costs come from `teyuna_core` (`TERRACE_COST`, `GREAT_TERRACE_COST`, `PATH_COST`, `WISDOM_CARD_COST`).

See [builder.py](../packages/sdk-python/src/teyuna_sdk/builder.py) for a complete agent that can win by building.

## Runnable example

Create a 3-player game, attach your bot, and fill the remaining seats with `teyuna-simulate` (or more agents in the same process). In another terminal, join the printed game id with sample agents:

```bash
teyuna-simulate join <uuid> --host http://127.0.0.1:8000 \
  builder:alice sleepy:bob
```

Alternatively, create the lobby with `teyuna-simulate create` (prints the game id), then join from your script with `GameLoop.join_existing(game_id, host)`.

## Sample agents

| Agent | Behavior |
| --- | --- |
| `builder` | Builds when it can afford settlements/paths |
| `skipper` | Advances / skips as soon as possible |
| `sleepy` | Sleeps and lets server timeouts drive play |
| `trader` | Proposes/accepts trades; skips elsewhere |

Source: [`packages/sdk-python/src/teyuna_sdk/`](../packages/sdk-python/src/teyuna_sdk/).
