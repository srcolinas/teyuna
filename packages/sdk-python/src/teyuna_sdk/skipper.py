import asyncio
import logging

import httpx2
import teyuna_shared

from . import entities
from .logging_config import agent_logger_name


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who will just skip all actions until the game
    is over. This player will never win the game, because it
    will never take any actions that give it points.
    """
    logger = logging.getLogger(agent_logger_name(context.nickname))
    sleep_time = 2
    while True:
        try:
            game = await context.client.get_game()
            turn_order = game.turn_order
            if turn_order and turn_order[0] == context.nickname:
                match game.phase:
                    case (
                        teyuna_shared.GamePhaseName.FIRST_PLACEMENT
                        | teyuna_shared.GamePhaseName.SECOND_PLACEMENT
                    ):
                        logger.info(
                            "%s skipping placement in phase %s",
                            context.nickname,
                            game.phase,
                        )
                        await context.client.add_initial_placements()
                    case _:
                        logger.info(
                            "%s skipping turn in phase %s",
                            context.nickname,
                            game.phase,
                        )
                        await context.client.advance_turn()
        except httpx2.HTTPError as exc:
            logger.error("%s failed to skip turn: %s", context.nickname, exc)
        await asyncio.sleep(sleep_time)
