import uuid
from typing import Protocol

from .. import entities, ports


class RetrieveGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> entities.ActiveGame: ...


def retrieve_game(
    id: uuid.UUID, /, *, repository: RetrieveGameRepository
) -> ports.ActiveGame | None:
    game = repository.retrieve(id)
    if game is None:
        return
    return ports.ActiveGame(
        id=id,
        map=game.map,
        conquistator_location=game.conquistator_location,
        players=[],
        settlements=[],
        paths=[],
    )
