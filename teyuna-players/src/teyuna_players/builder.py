import asyncio
from typing import Awaitable

from . import events


def build(queue: asyncio.Queue[events.ActionExecutionResult], token: str) -> Awaitable[None]:
    """
    A player who will build the best possible structures
    given its current resources. This player can win the game
    as building is one of the ways to get points and by
    taking building actions alone a player can reach the
    desired goal of 10 points.
    """

    async def helper() -> None: ...
