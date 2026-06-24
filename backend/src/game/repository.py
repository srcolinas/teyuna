import collections
import datetime
import uuid

from . import entities


class GameDoesNotExistError(Exception): ...


class UsernameAlreadyExists(Exception): ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._proposed: dict[uuid.UUID, entities.ProposedGame] = {}
        self._active: dict[uuid.UUID, entities.ActiveGame] = {}

    def add(
        self, *, num_players: int, expires_at: datetime.datetime
    ) -> entities.ProposedGame:
        game = entities.ProposedGame(
            id=uuid.uuid4(),
            max_players=num_players,
            expires_at=expires_at,
            players=set(),
        )
        self._proposed[game.id] = game
        return game

    def retrieve(self, id: uuid.UUID) -> entities.ActiveGame | None:
        return self._active.get(id)

    def start(self, id: uuid.UUID, map: entities.Map) -> None:
        proposed = self._proposed.pop(id)
        active = entities.ActiveGame(
            map=map,
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
        if username in game.players:
            raise UsernameAlreadyExists
        game.players.add(username)
        return game

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._proposed:
            raise GameDoesNotExistError
