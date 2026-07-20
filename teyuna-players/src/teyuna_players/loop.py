import asyncio
import uuid
from typing import Protocol, Self

from . import events


class Player(Protocol):
    async def take_action(
        self, queue: asyncio.Queue[events.ActionExecutionResult]
    ) -> None: ...


class GameLoop:
    @classmethod
    def create(cls) -> Self:
        raise NotImplementedError

    def __init__(self, game_id: uuid.UUID) -> None:
        self._game_id = game_id

    def subscribe(self, player: Player) -> None:
        asyncio.create_task(player.take_action(self._queue))

    async def run(self) -> None:
        raise NotImplementedError