import asyncio
import uuid
from typing import Self

import httpx
import httpx_sse

from . import events


class GameLoop:
    @classmethod
    def create(cls) -> Self:
        raise NotImplementedError

    def __init__(self, game_id: uuid.UUID, host: str) -> None:
        self._game_id = game_id
        self._host = host
        self._listeners = set[asyncio.Queue[events.ActionExecutionResult]]()

    @property
    def game_id(self) -> uuid.UUID:
        return self._game_id

    async def add_player(
        self, nickname: str
    ) -> tuple[asyncio.Queue[events.ActionExecutionResult], str]:
        with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._host}/proposed-games/{self._game_id}/players",
                json={"nickname": nickname},
            )
            response.raise_for_status()
            
        queue = asyncio.Queue()
        self._listeners.add(queue)
        return queue, nickname

    async def run(self, event: events.ActionExecutionResult) -> None:
        async with httpx.AsyncClient() as client:
            async with httpx_sse.aconnect_sse(
                client, "GET", f"{self._host}/active-games/{self._game_id}/events"
            ) as source:
                async for event in source:
                    parsed = events.ActionExecutionResult.model_validate_json(event.data)
                    for listener in self._listeners:
                        await listener.put(parsed)
