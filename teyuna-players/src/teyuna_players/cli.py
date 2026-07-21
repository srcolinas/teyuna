import argparse
import asyncio
import uuid
from typing import Protocol, Awaitable

from . import builder, skipper, sleepy, loop, events


class PlayerBuilder(Protocol):
    def __call__(
        self, queue: asyncio.Queue[events.ActionExecutionResult], token: str
    ) -> Awaitable[None]: ...


def main() -> None:
    parser = argparse.ArgumentParser("Creates up to 4 players to play a game of Teyuna")
    parser.add_argument(
        "--game-id",
        type=uuid.UUID | None,
        default=None,
        help="if not provided, a new game will be created. If provided, the players will join the existing game.",
    )
    parser.add_argument(
        "players",
        nargs="*",
        default=["builder"] * 3,
        help="names of the agents to play with. If not provided, a dumb player will be created.",
    )
    args = parser.parse_args()
    asyncio.run(helper(args.game_id, args.host, args.players))


async def helper(game_id: uuid.UUID | None, host: str, players: list[str]) -> None:
    if game_id is None:
        game = loop.GameLoop.create(host=host)
    else:
        game = loop.GameLoop(game_id, host)

    player_tasks = []
    for cls_ in players:
        queue, token = await game.add_player(cls_)
        builder = _BUILDERS[cls_]
        player = builder(queue, token)
        player_tasks.append(asyncio.create_task(player))
    game_task = asyncio.create_task(game.run())
    await asyncio.gather(game_task, *player_tasks)


_BUILDERS: dict[str, PlayerBuilder] = {
    "sleepy": sleepy.build,
    "skipper": skipper.build,
    "builder": builder.build,
}
