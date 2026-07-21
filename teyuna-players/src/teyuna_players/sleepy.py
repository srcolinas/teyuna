import asyncio
from typing import Awaitable

from . import events


def build(
    queue: asyncio.Queue[events.ActionExecutionResult], token: str
) -> Awaitable[None]:
    """
    A player who doesn't really do anything. Just
    waiting there for the game to finish and the server
    take actions on its behalf. It will never win the
    game, because it won't take any actions that
    give it points.
    """

    async def helper() -> None: ...
