import collections
import datetime
import uuid

from . import entities


class GameDoesNotExistError(Exception): ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._proposed: dict[uuid.UUID, entities.ProposedGame] = {}
        self._active: dict[uuid.UUID, entities.ActiveGame] = {}

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
        self._proposed[game.id] = game
        return game

    def retrieve(self, id: uuid.UUID) -> entities.ActiveGame | None:
        return self._active.get(id)

    def start(self, id: uuid.UUID) -> None:
        proposed = self._proposed.pop(id)
        active = entities.ActiveGame(
            map=proposed.map,
            players={
                username: entities.Player(
                    cards=collections.Counter(),
                    played_cards=collections.Counter(),
                    resources=collections.Counter(),
                    settlements=[],
                    paths=[],
                )
                for username in proposed.players
            },
        )
        self._active[id] = active

    def retrieve_proposed(self, id: uuid.UUID) -> entities.ProposedGame:
        self._validate_game_exists(id)
        return self._proposed[id]

    def add_player(self, game_id: uuid.UUID, username: str) -> entities.ProposedGame:
        self._validate_game_exists(game_id)
        game = self._proposed[game_id]
        game.players.append(username)
        return game

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._proposed:
            raise GameDoesNotExistError
