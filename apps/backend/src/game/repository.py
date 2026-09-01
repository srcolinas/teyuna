import uuid
from collections.abc import Iterable

from . import entities


class GameDoesNotExistError(Exception): ...


class InMemoryGameRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, entities.Game] = {}

    def retrieve(self, id: uuid.UUID) -> entities.Game:
        self._validate_game_exists(id)
        return self._memory[id]

    def add(
        self,
        game: entities.Game,
    ) -> uuid.UUID:
        id = uuid.uuid4()
        self._memory[id] = game
        return id

    def update(
        self,
        id: uuid.UUID,
        game: entities.Game,
    ) -> None:
        self._validate_game_exists(id)
        self._memory[id] = game

    def items(self) -> Iterable[tuple[uuid.UUID, entities.Game]]:
        return tuple(self._memory.items())

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise GameDoesNotExistError
