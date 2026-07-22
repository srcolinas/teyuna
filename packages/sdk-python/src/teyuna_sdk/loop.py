import logging
import uuid
from typing import Self

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
        client = sdk.GameClient(host)
        game = await client.create_game(num_players)
        logger.info("Created game %s for %s players", game.id, num_players)
        return cls(game.id, client)

    @classmethod
    def join_existing(cls, game_id: uuid.UUID, host: str) -> Self:
        """Bind to an existing game without creating a new one."""
        return cls(game_id, sdk.GameClient(host))

    async def add_player(self, nickname: str) -> entities.PlayerContext:
        """Join the game as ``nickname`` and return an authenticated context."""
        client = await self._client.join_game(self._game_id, nickname)
        logger.info("Player %s joined game %s", nickname, self._game_id)
        return entities.PlayerContext(
            nickname=nickname,
            game_id=self._game_id,
            client=client,
        )

    async def run(self) -> None:
        """Stream and log SSE events until the connection ends."""
        async for event in self._client.stream_events(self._game_id):
            logger.info("GameLoop event: %s", event)
