import argparse
import asyncio
import logging
import uuid
from pathlib import Path

from . import builder, entities, loop, skipper, sleepy, stochastic
from .logging_config import (
    configure_logging,
    ensure_agent_logger,
    ensure_game_loop_logger,
    resolve_log_dir,
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


def _add_host_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default="http://127.0.0.1:8000",
        help="base URL of the Teyuna game server",
    )


def _add_logdir_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--logdir",
        type=Path,
        default=None,
        help="directory for agent/game-loop log files "
        "(default: logs/<YYYY-MM-DD-HH-MM>)",
    )


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(
        "teyuna-simulate",
        description="Create a Teyuna game or join with simulated agents",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create",
        help="create a new game and print its id",
    )
    _add_host_argument(create_parser)
    _add_logdir_argument(create_parser)
    create_parser.add_argument(
        "--num-players",
        type=int,
        choices=(3, 4),
        default=3,
        help="number of seats in the lobby (default: 3)",
    )
    create_parser.set_defaults(func=_cmd_create)

    join_parser = subparsers.add_parser(
        "join",
        help="join an existing game with 1–4 agents",
    )
    join_parser.add_argument(
        "game_id",
        type=_parse_uuid,
        help="id of the game to join",
    )
    _add_host_argument(join_parser)
    _add_logdir_argument(join_parser)
    join_parser.add_argument(
        "players",
        nargs="+",
        type=_parse_player,
        help="agents as 'name' or 'name:nickname' (1–4)",
    )
    join_parser.set_defaults(func=_cmd_join)

    args = parser.parse_args()
    if args.command == "join" and not 1 <= len(args.players) <= 4:
        join_parser.error("join requires between 1 and 4 player specs")
    args.func(args)


def _cmd_create(args: argparse.Namespace) -> None:
    asyncio.run(_create(args.host, args.num_players))


def _cmd_join(args: argparse.Namespace) -> None:
    logdir = resolve_log_dir(args.logdir)
    ensure_game_loop_logger(logdir=logdir)
    for _, nickname in args.players:
        ensure_agent_logger(nickname, logdir=logdir)
    asyncio.run(_join(args.game_id, args.host, args.players))


async def _create(host: str, num_players: int) -> None:
    game = await loop.GameLoop.create(host=host, num_players=num_players)
    print(game.game_id)


async def _join(game_id: uuid.UUID, host: str, players: list[tuple[str, str]]) -> None:
    game = loop.GameLoop.join_existing(game_id, host)

    contexts: list[tuple[str, entities.PlayerContext]] = []
    for agent, nickname in players:
        if agent not in _BUILDERS:
            raise ValueError(f"unknown player agent: {agent!r}")
        context = await game.add_player(nickname)
        contexts.append((agent, context))

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
    "stochastic": stochastic.build,
}


if __name__ == "__main__":
    main()
