import asyncio
import logging
import random

import teyuna_core

from . import discard, entities
from .logging_config import agent_logger_name

_RNG = random.Random()


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who will just skip all actions until the game
    is over. This player will never win the game, because it
    will never take any actions that give it points.
    """
    logger = logging.getLogger(agent_logger_name(context.nickname))
    logger.info(
        "Skipper %s (token: %s) joined game %s",
        context.nickname,
        context.client.token,
        context.client.game_id,
    )
    sleep_time = 2
    while True:
        game = await context.client.get_game()
        if await discard.discard_if_required(context, logger, game, _RNG):
            await asyncio.sleep(sleep_time)
            continue
        if (
            game.turn_order
            and game.turn_order[0] == context.nickname
            and game.phase is not teyuna_core.GamePhaseName.DISCARD_RESOURCES
        ):
            logger.info(
                "%s skipping turn in phase %s",
                context.nickname,
                game.phase,
            )
            await context.client.submit_action(teyuna_core.PlayerAction())
        await asyncio.sleep(sleep_time)
