import datetime
import uuid
from typing import Protocol

import pydantic

from ... import player, active
from .. import entities


class GameAlreadyFullError(Exception): ...


class GameExpiredError(Exception): ...


class AddPlayerGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> entities.ProposedGame: ...

    def add_player(
        self, game_id: uuid.UUID, nickname: player.Nickname
    ) -> entities.ProposedGame: ...


class PlayerAddedResult(pydantic.BaseModel):
    proposed: entities.ProposedGame
    game: uuid.UUID | None = None


def add_player(
    *,
    game_id: uuid.UUID,
    nickname: player.Nickname,
    repository: AddPlayerGameRepository,
    game_manager: active.services.GameManager,
    auth: player.PlayerAuthenticationService,
) -> tuple[PlayerAddedResult, player.Token]:
    game = repository.retrieve(game_id)
    if len(game.players) >= game.max_players:
        raise GameAlreadyFullError

    if game.expires_at < datetime.datetime.now():
        raise GameExpiredError

    token = auth.add(nickname)
    proposed = repository.add_player(game_id=game_id, nickname=nickname)
    if proposed.max_players == len(proposed.players):
        id = game_manager.create_game(players=tuple(proposed.players))
        return PlayerAddedResult(proposed=proposed, game=id), token
    return PlayerAddedResult(proposed=proposed), token
