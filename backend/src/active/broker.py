import asyncio
import collections
import dataclasses
import uuid
from collections.abc import AsyncGenerator

from . import actions


@dataclasses.dataclass
class Event:
    id: int
    data: actions.ActionExecutionResult


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[Event]]] = (
            collections.defaultdict(set)
        )
        self._next_id: dict[uuid.UUID, int] = collections.defaultdict(int)

    async def publish(
        self, game_id: uuid.UUID, data: actions.ActionExecutionResult
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
