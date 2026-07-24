# Teyuna SDK

Python SDK for talking to a [Teyuna](https://github.com/srcolinas/teyuna) game server: create and join games, take turns, and build your own AI agents.

## Requirements

- Python 3.14+
- A running Teyuna game server (see the [main repository](https://github.com/srcolinas/teyuna))

## Install

```bash
pip install teyuna-sdk
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add teyuna-sdk
```

## Quick start

Create a game, join as a player, and perform actions with the async HTTP client:

```python
import asyncio

import teyuna_shared
from teyuna_sdk.sdk import GameClient


async def main() -> None:
    client = await GameClient.create_game("http://127.0.0.1:8000", num_players=3)
    await client.authenticate("explorer")

    game = await client.get_game()
    print(f"Joined game {client.game_id} as explorer")
    print(f"Phase: {game.phase}")

    # Authenticated actions use the token stored by authenticate.
    # Example: advance the turn when it is your turn.
    # result = await client.submit_action(teyuna_shared.PlayerAction())


asyncio.run(main())
```

### Build a custom agent

Agents are async callables that receive a `PlayerContext` (nickname, game id, and authenticated client). Use `GameLoop` to create or join a game and attach players:

```python
import asyncio

import teyuna_shared
from teyuna_sdk import entities, loop


async def my_agent(*, context: entities.PlayerContext) -> None:
    while True:
        game = await context.client.get_game()
        if not game.turn_order or game.turn_order[0] != context.nickname:
            await asyncio.sleep(1)
            continue

        if game.phase is teyuna_shared.GamePhaseName.DICE_ROLL:
            await context.client.submit_action(teyuna_shared.PlayerAction())
        else:
            await asyncio.sleep(1)


async def main() -> None:
    game = await loop.GameLoop.create(host="http://127.0.0.1:8000", num_players=3)
    context = await game.add_player("my-bot")
    await asyncio.gather(game.run(), my_agent(context=context))


asyncio.run(main())
```

## Sample agents

The package ships with simple agents you can use as templates or opponents:

| Agent | Behavior |
| --- | --- |
| `builder` | Builds terraces, great terraces, and paths when it can |
| `skipper` | Advances the turn as soon as possible |
| `sleepy` | Waits and lets server timeouts drive the game |
| `stochastic` | Chooses random actions across phases |

## CLI: simulate a game

After installing the package, run a local simulation against a game server:

```bash
# Create a new game (prints only the game id)
teyuna-simulate create --host http://127.0.0.1:8000

# Join with 1–4 agents (agent or agent:nickname)
teyuna-simulate join <uuid> --host http://127.0.0.1:8000 \
  builder:alice sleepy:bob skipper:carol

# Custom log directory
teyuna-simulate join <uuid> --logdir ./my-run-logs \
  builder:alice sleepy:bob skipper:carol

# Four-seat lobby, then join
teyuna-simulate create --host http://127.0.0.1:8000 --num-players 4
teyuna-simulate join <uuid> builder sleepy skipper builder:builder-2
```

## Development

From this directory:

```bash
make setup    # sync deps and install pre-commit
make format
make lint
make check
```

Publish to PyPI (maintainers):

```bash
make publish
```

## License

MIT — see [LICENSE](LICENSE).
