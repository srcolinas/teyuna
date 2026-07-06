import uuid
from collections.abc import Sequence
from typing import Protocol

from ... import player
from .. import _entities


class ManagedGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> _entities.ActiveGame: ...

    def add(self, game: _entities.ActiveGame) -> uuid.UUID: ...


class GameManager:
    def __init__(self, repository: ManagedGameRepository) -> None:
        self._repository = repository

    def start(
        self,
        players: Sequence[player.Nickname],
    ) -> uuid.UUID:
        game = _entities.ActiveGame.create_new(players)
        return self._repository.add(game)

    def add_terrace(
        self,
        id: uuid.UUID,
        nickname: player.Nickname,
        *,
        q: int,
        r: int,
        direction: int,
    ) -> _entities.Settlement:
        game = self._repository.retrieve(id)
        settlement = game.add_terrace(nickname, q=q, r=r, direction=direction)
        return settlement
