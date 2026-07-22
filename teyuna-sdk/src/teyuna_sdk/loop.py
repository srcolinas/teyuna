import logging
import uuid
from typing import Self

from . import entities, sdk

logger = logging.getLogger(__name__)


class GameLoop:
    def __init__(self, game_id: uuid.UUID, client: sdk.GameClient) -> None:
        self._game_id = game_id
        self._client = client

    @classmethod
    async def create(
        cls,
        host: str,
        *,
        num_players: int = 3,
    ) -> Self:
        client = sdk.GameClient(host)
        game = await client.create_game(num_players)
        logger.info("Created game %s for %s players", game.id, num_players)
        return cls(game.id, client)

    @classmethod
    def join_existing(cls, game_id: uuid.UUID, host: str) -> Self:
        return cls(game_id, sdk.GameClient(host))

    async def add_player(self, nickname: str) -> entities.PlayerContext:
        client = await self._client.join_game(self._game_id, nickname)
        logger.info("Player %s joined game %s", nickname, self._game_id)
        return entities.PlayerContext(
            nickname=nickname,
            game_id=self._game_id,
            client=client,
        )

    async def run(self) -> None:
        async for event in self._client.stream_events(self._game_id):
            logger.info("GameLoop event: %s", event)
