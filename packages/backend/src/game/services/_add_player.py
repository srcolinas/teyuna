import datetime
import uuid
from typing import Protocol

from .. import player, ports, entities
from . import _retrieve


class UpdateGameRepository(_retrieve.RetrieveGameRepository, Protocol):
    def update(
        self,
        id: uuid.UUID,
        game: entities.Game,
    ) -> None: ...


class GameAlreadyStartedError(Exception):
    pass


def add_player(
    *,
    game_id: uuid.UUID,
    nickname: player.Nickname,
    repository: UpdateGameRepository,
    auth: player.PlayerAuthenticationService,
    first_placement_timeout: datetime.timedelta,
) -> tuple[ports.Game, player.Token]:
    game = repository.retrieve(game_id)
    if game.phase is not entities.GamePhaseName.LOBBY:
        raise GameAlreadyStartedError("game already started")
    token = auth.add(nickname)
    game.add_player(nickname)
    if game.available_slots <= 0:
        game.start(first_placement_timeout)
    repository.update(game_id, game)
    return _retrieve.retrieve_game(game_id, repository=repository), token
