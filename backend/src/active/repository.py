import uuid

from . import entities


class ActiveGameDoesNotExistError(Exception): ...


class InMemoryActiveGameRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, entities.ActiveGame] = {}

    def retrieve(self, id: uuid.UUID) -> entities.ActiveGame:
        self._validate_game_exists(id)
        return self._memory[id]

    def add(self, game: entities.ActiveGame) -> uuid.UUID:
        id = uuid.uuid4()
        self._memory[id] = game
        return id

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise ActiveGameDoesNotExistError
