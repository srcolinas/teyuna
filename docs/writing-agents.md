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
3. If `game.turn_order[0] != context.nickname` — sleep and poll again.
4. Otherwise dispatch on `game.phase` and call the matching client method.
5. Optionally call `await context.client.get_hand()` for private resources and cards.

You can also subscribe to SSE via `GameClient.stream_events()` (what `GameLoop.run()` does) and still poll `get_game` / `get_hand` before acting.

## Phase → action cheat sheet

| Phase | Typical SDK call |
| --- | --- |
| `first placement` / `second placement` | `add_initial_placements(terrace=..., path=...)` (omit both to skip) |
| `dice roll` | `advance_turn()` (roll) or `play_wisdom_card(...)` |
| `discard resources` | `discard_resources(count)` using `game.to_discard_resources[nickname]` |
| `move conquistator` / `* play warrior` | `move_conquistator(location, take_from=...)` |
| `* play mamo` | `play_mamo(resource)` |
| `* play blessed` | `play_blessing((r1, r2))` |
| `* play pathfinder` | `play_pathfinder(paths)` |
| `trade and build` | `build_settlement`, `build_path`, `buy_wisdom_card`, trades, then `advance_turn()` |
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

Building costs live in `teyuna_shared` (`TERRACE_COST`, `GREAT_TERRACE_COST`, `PATH_COST`, `WISDOM_CARD_COST`).

See [builder.py](../packages/sdk-python/src/teyuna_sdk/builder.py) for a complete agent that can win by building.

## Runnable example

Create a 3-player game, attach your bot, and fill the remaining seats with `teyuna-simulate` (or more agents in the same process).

```python
import asyncio

import teyuna_shared
from teyuna_sdk import entities, loop, rules


async def my_agent(*, context: entities.PlayerContext) -> None:
    while True:
        game = await context.client.get_game()
        if not game.turn_order or game.turn_order[0] != context.nickname:
            await asyncio.sleep(1)
            continue

        match game.phase:
            case (
                teyuna_shared.GamePhaseName.FIRST_PLACEMENT
                | teyuna_shared.GamePhaseName.SECOND_PLACEMENT
            ):
                vertices = rules.vertices_available_for_free_placement(game)
                terrace = vertices[0]
                path = rules.edges_for_free_placement(game, terrace)[0]
                await context.client.add_initial_placements(
                    terrace=terrace, path=path
                )
            case teyuna_shared.GamePhaseName.DICE_ROLL:
                await context.client.advance_turn()
            case teyuna_shared.GamePhaseName.TRADE_AND_BUILD:
                await context.client.advance_turn()
            case teyuna_shared.GamePhaseName.END_GAME:
                return
            case _:
                await asyncio.sleep(1)


async def main() -> None:
    host = "http://127.0.0.1:8000"
    game = await loop.GameLoop.create(host=host, num_players=3)
    print(f"Game id: {game.game_id}")  # share this with opponents / CLI
    ctx = await game.add_player("my-bot")
    await asyncio.gather(game.run(), my_agent(context=ctx))


if __name__ == "__main__":
    asyncio.run(main())
```

### Fill the other seats

In another terminal, join the printed game id with sample agents:

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
| `stochastic` | Picks random legal-ish actions across phases |

Source: [`packages/sdk-python/src/teyuna_sdk/`](../packages/sdk-python/src/teyuna_sdk/).
