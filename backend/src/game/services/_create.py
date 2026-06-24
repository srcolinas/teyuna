import datetime
from typing import Protocol

from .. import entities, ports


class CreateGameRepository(Protocol):
    def add(
        self, *, num_players: int, expires_at: datetime.datetime
    ) -> entities.ProposedGame: ...


def create_game(
    params: ports.CreateGameRequest,
    repository: CreateGameRepository,
    expires_in: datetime.timedelta = datetime.timedelta(seconds=60),
) -> entities.ProposedGame:
    return repository.add(
        num_players=params.num_players,
        expires_at=datetime.datetime.now() + expires_in,
    )
