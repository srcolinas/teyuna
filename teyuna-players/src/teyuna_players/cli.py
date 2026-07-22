import argparse
import asyncio
import logging
import uuid

from . import builder, entities, loop, skipper, sleepy, trader
from .logging_config import (
    configure_logging,
    ensure_agent_logger,
    ensure_game_loop_logger,
)

logger = logging.getLogger(__name__)


def _parse_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _parse_player(value: str) -> tuple[str, str]:
    """Parse ``agent`` or ``agent:nickname`` into (agent, nickname)."""
    if ":" in value:
        agent, nickname = value.split(":", 1)
        if not agent or not nickname:
            raise argparse.ArgumentTypeError(
                f"invalid player {value!r}; expected agent or agent:nickname"
            )
        return agent, nickname
    return value, value


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser("Creates up to 4 players to play a game of Teyuna")
    parser.add_argument(
        "--game-id",
        type=_parse_uuid,
        default=None,
        help="if not provided, a new game will be created. If provided, the players will join the existing game.",
    )
    parser.add_argument(
        "--host",
        default="http://127.0.0.1:8000",
        help="base URL of the Teyuna game server",
    )
    parser.add_argument(
        "--show-tokens",
        action="store_true",
        help="print player session tokens for the optional private observer UI; treat them as credentials",
    )
    parser.add_argument(
        "players",
        nargs="*",
        type=_parse_player,
        default=[
            ("builder", "builder"),
            ("sleepy", "sleepy"),
            ("skipper", "skipper"),
        ],
        help="agents as 'name' or 'name:nickname' (default: builder, sleepy, skipper)",
    )
    args = parser.parse_args()
    ensure_game_loop_logger()
    for _, nickname in args.players:
        ensure_agent_logger(nickname)
    asyncio.run(helper(args.game_id, args.host, args.players, args.show_tokens))


async def helper(
    game_id: uuid.UUID | None,
    host: str,
    players: list[tuple[str, str]],
    show_tokens: bool = False,
) -> None:
    if game_id is None:
        game = await loop.GameLoop.create(host=host, num_players=len(players))
    else:
        game = loop.GameLoop.join_existing(game_id, host)

    contexts: list[tuple[str, entities.PlayerContext]] = []
    for agent, nickname in players:
        if agent not in _BUILDERS:
            raise ValueError(f"unknown player agent: {agent!r}")
        context = await game.add_player(nickname)
        contexts.append((agent, context))
        if show_tokens:
            logger.warning(
                "PRIVATE TOKEN for %s: %s",
                nickname,
                context.client.session_token,
            )

    tasks: list[asyncio.Task[None]] = [
        asyncio.create_task(
            _BUILDERS[agent](context=context),
            name=f"{agent}:{context.nickname}",
        )
        for agent, context in contexts
    ]
    game_task = asyncio.create_task(game.run(), name="game-loop")
    logger.info("Running %s agents against %s", len(tasks), host)
    try:
        await asyncio.gather(game_task, *tasks)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


_BUILDERS: dict[str, entities.PlayerBuilder] = {
    "sleepy": sleepy.build,
    "skipper": skipper.build,
    "builder": builder.build,
    "trader": trader.build,
}


if __name__ == "__main__":
    main()
