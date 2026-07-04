import uuid

from . import _entities


class ActiveGameDoesNotExistError(Exception): ...


class InMemoryActiveGameRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, _entities.ActiveGame] = {}

    def retrieve(self, id: uuid.UUID) -> _entities.ActiveGame | None:
        return self._memory.get(id)

    def add(self, game: _entities.ActiveGame) -> uuid.UUID:
        id = uuid.uuid4()
        self._memory[id] = game
        return id

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise ActiveGameDoesNotExistError
