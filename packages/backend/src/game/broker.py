import asyncio
import collections
import dataclasses
import uuid
from collections.abc import AsyncGenerator

import teyuna_core


@dataclasses.dataclass
class Event:
    id: int
    data: teyuna_core.ActionExecutionResult


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[Event]]] = (
            collections.defaultdict(set)
        )
        self._next_id: dict[uuid.UUID, int] = collections.defaultdict(int)

    async def publish(
        self, game_id: uuid.UUID, data: teyuna_core.ActionExecutionResult
    ) -> None:
        event = Event(id=self._next_id[game_id], data=data)
        self._next_id[game_id] += 1
        for queue in tuple(self._subscribers[game_id]):
            queue.put_nowait(event)

    async def iterate(self, game_id: uuid.UUID) -> AsyncGenerator[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[game_id].add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[game_id].discard(queue)
