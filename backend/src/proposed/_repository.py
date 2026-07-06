import datetime
import uuid

from .. import player
from . import _entities


class ProposedGameDoesNotExistError(Exception): ...


class NicknameAlreadyExists(Exception): ...


class InMemoryProposedGameRepository:
    def __init__(self) -> None:
        self._proposed: dict[uuid.UUID, _entities.ProposedGame] = {}

    def add(
        self, *, num_players: int, expires_at: datetime.datetime
    ) -> _entities.ProposedGame:
        game = _entities.ProposedGame(
            id=uuid.uuid4(),
            max_players=num_players,
            expires_at=expires_at,
            players=set(),
        )
        self._proposed[game.id] = game
        return game

    def retrieve(self, id: uuid.UUID) -> _entities.ProposedGame:
        self._validate_game_exists(id)
        return self._proposed[id]

    def add_player(
        self, game_id: uuid.UUID, nickname: player.Nickname
    ) -> _entities.ProposedGame:
        self._validate_game_exists(game_id)
        game = self._proposed[game_id]
        if nickname in game.players:
            raise NicknameAlreadyExists
        game.players.add(nickname)
        return game

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._proposed:
            raise ProposedGameDoesNotExistError
