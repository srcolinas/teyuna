import dataclasses
import datetime
import uuid
from collections.abc import Iterable

from . import entities, actions


class ActiveGameDoesNotExistError(Exception): ...


@dataclasses.dataclass
class StoredActiveGame:
    game: entities.ActiveGame
    phase: actions.GamePhaseName
    phase_deadline: datetime.datetime | None


class InMemoryActiveGameRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, StoredActiveGame] = {}

    def retrieve(self, id: uuid.UUID) -> StoredActiveGame:
        self._validate_game_exists(id)
        return self._memory[id]

    def add(
        self,
        game: entities.ActiveGame,
        *,
        phase_deadline: datetime.datetime | None,
    ) -> uuid.UUID:
        id = uuid.uuid4()
        self._memory[id] = StoredActiveGame(
            game=game,
            phase=actions.GamePhaseName.FIRST_PLACEMENT,
            phase_deadline=phase_deadline,
        )
        return id

    def update(
        self,
        id: uuid.UUID,
        game: entities.ActiveGame,
        phase: actions.GamePhaseName,
        phase_deadline: datetime.datetime | None,
    ) -> None:
        self._validate_game_exists(id)
        self._memory[id] = StoredActiveGame(
            game=game, phase=phase, phase_deadline=phase_deadline
        )

    def items(self) -> Iterable[tuple[uuid.UUID, StoredActiveGame]]:
        return tuple(self._memory.items())

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise ActiveGameDoesNotExistError
