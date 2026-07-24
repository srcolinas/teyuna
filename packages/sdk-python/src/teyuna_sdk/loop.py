import asyncio
import logging
import uuid
from typing import Self

import teyuna_shared

from . import entities, sdk

logger = logging.getLogger(__name__)


class GameLoop:
    """Create or join a game and attach agents that share one SSE event stream."""

    def __init__(self, game_id: uuid.UUID, client: sdk.GameClient) -> None:
        self._game_id = game_id
        self._client = client

    @property
    def game_id(self) -> uuid.UUID:
        """UUID of the game this loop is bound to."""
        return self._game_id

    @classmethod
    async def create(
        cls,
        host: str,
        *,
        num_players: int = 3,
    ) -> Self:
        """Create a new game on ``host`` and return a loop bound to it."""
        client = await sdk.GameClient.create_game(host, num_players)
        logger.info("Created game %s for %s players", client.game_id, num_players)
        return cls(client.game_id, client)

    @classmethod
    def join_existing(cls, game_id: uuid.UUID, host: str) -> Self:
        """Bind to an existing game without creating a new one."""
        logger.info("Joining existing game %s on %s", game_id, host)
        return cls(game_id, sdk.GameClient(host, game_id))

    async def add_player(self, nickname: str) -> entities.PlayerContext:
        """Join the game as ``nickname`` and return an authenticated context."""
        client = await sdk.GameClient(
            self._client._base_url, self._game_id
        ).authenticate(nickname)
        logger.info("Player %s joined game %s", nickname, self._game_id)
        return entities.PlayerContext(
            nickname=nickname,
            game_id=self._game_id,
            client=client,
        )

    async def _wait_until_active(self) -> None:
        """Block until the lobby closes; ``/events`` rejects lobby-phase games."""
        while True:
            state = await self._client.get_game()
            if state.phase is not teyuna_shared.GamePhaseName.LOBBY:
                return
            logger.info("Waiting for game to start...")
            await asyncio.sleep(2)

    async def run(self) -> None:
        """Stream and log SSE events until the connection ends."""
        await self._wait_until_active()
        async for event in self._client.stream_events():
            logger.info("GameLoop event: %s", event.model_dump_json())
