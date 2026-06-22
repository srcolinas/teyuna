import datetime
import uuid
from typing import Protocol

from .. import entities


class GameAlreadyFullError(Exception): ...


class GameExpiredError(Exception): ...


class AddPlayerGameRepository(Protocol):
    def retrieve_proposed(self, id: uuid.UUID) -> entities.ProposedGame: ...

    def add_player(
        self, game_id: uuid.UUID, username: str
    ) -> entities.ProposedGame: ...


def add_player(
    *,
    game_id: uuid.UUID,
    username: str,
    repository: AddPlayerGameRepository,
) -> entities.ProposedGame:
    game = repository.retrieve_proposed(game_id)
    if len(game.players) >= game.max_players:
        raise GameAlreadyFullError

    if game.expires_at < datetime.datetime.now():
        raise GameExpiredError

    return repository.add_player(game_id=game_id, username=username)
