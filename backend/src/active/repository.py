import uuid

from . import entities, actions


class ActiveGameDoesNotExistError(Exception): ...


type Game = tuple[entities.ActiveGame, actions.GamePhaseName]


class InMemoryActiveGameRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, Game] = {}

    def retrieve(self, id: uuid.UUID) -> Game:
        self._validate_game_exists(id)
        return self._memory[id]

    def add(self, game: entities.ActiveGame) -> uuid.UUID:
        id = uuid.uuid4()
        self._memory[id] = (game, actions.GamePhaseName.FIRST_PLACEMENT)
        return id

    def update(
        self, id: uuid.UUID, game: entities.ActiveGame, phase: actions.GamePhaseName
    ) -> None:
        self._validate_game_exists(id)
        self._memory[id] = (game, phase)

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise ActiveGameDoesNotExistError
