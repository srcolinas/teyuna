import datetime
import uuid
from typing import Protocol

import pydantic

from ... import player
from .. import _entities


class GameAlreadyFullError(Exception): ...


class GameExpiredError(Exception): ...


class AddPlayerGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> _entities.ProposedGame: ...

    def add_player(
        self, game_id: uuid.UUID, username: str
    ) -> _entities.ProposedGame: ...


class PlayerAddedResult(pydantic.BaseModel):
    proposed: _entities.ProposedGame
    game: uuid.UUID | None = None


class GameManager(Protocol):
    def start(self, players: tuple[str, ...]) -> uuid.UUID: ...


def add_player(
    *,
    game_id: uuid.UUID,
    username: str,
    repository: AddPlayerGameRepository,
    manager: GameManager,
    auth: player.PlayerAuthenticationService,
) -> tuple[PlayerAddedResult, player.Token]:
    game = repository.retrieve(game_id)
    if len(game.players) >= game.max_players:
        raise GameAlreadyFullError

    if game.expires_at < datetime.datetime.now():
        raise GameExpiredError

    token = auth.add(username)
    proposed = repository.add_player(game_id=game_id, username=username)
    if proposed.max_players == len(proposed.players):
        id = manager.start(players=tuple(proposed.players))
        return PlayerAddedResult(proposed=proposed, game=id), token
    return PlayerAddedResult(proposed=proposed), token
