import asyncio
from typing import Awaitable

from . import events


def build(queue: asyncio.Queue[events.ActionExecutionResult], token: str) -> Awaitable[None]:
    """
    A player who will just skip all actions until the game
    is over. This player will never win the game, because it
    will never take any actions that give it points.
    """

    async def helper() -> None: ...
