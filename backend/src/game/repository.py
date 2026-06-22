import datetime
import uuid

from . import entities


class GameDoesNotExistError(Exception): ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._memory: dict[uuid.UUID, entities.ProposedGame] = {}

    def add(
        self, *, num_players: int, map: entities.Map, expires_at: datetime.datetime
    ) -> entities.ProposedGame:
        game = entities.ProposedGame(
            id=uuid.uuid4(),
            map=map,
            max_players=num_players,
            expires_at=expires_at,
            players=[],
        )
        self._memory[game.id] = game
        return game

    def retrieve_proposed(self, id: uuid.UUID) -> entities.ProposedGame:
        self._validate_game_exists(id)
        return self._memory[id]

    def add_player(self, game_id: uuid.UUID, username: str) -> entities.ProposedGame:
        self._validate_game_exists(game_id)
        game = self._memory[game_id]
        game.players.append(entities.AwaitingPlayer(id=uuid.uuid4(), username=username))
        return game

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._memory:
            raise GameDoesNotExistError
