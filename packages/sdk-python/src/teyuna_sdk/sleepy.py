import asyncio
import logging

from . import entities
from .logging_config import agent_logger_name


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who doesn't really do anything. Just
    waiting there for the game to finish and the server
    take actions on its behalf. It will never win the
    game, because it won't take any actions that
    give it points.
    """
    logger = logging.getLogger(agent_logger_name(context.nickname))
    while True:
        logger.info("%s still waiting for server timeouts", context.nickname)
        await asyncio.sleep(10)
