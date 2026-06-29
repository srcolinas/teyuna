import datetime
import random
import uuid
from typing import Protocol

from .. import entities
from ._generate_map import generate_map


class GameAlreadyFullError(Exception): ...


class GameExpiredError(Exception): ...


class AddPlayerGameRepository(Protocol):
    def retrieve_proposed(self, id: uuid.UUID) -> entities.ProposedGame: ...

    def add_player(
        self, game_id: uuid.UUID, username: str
    ) -> entities.ProposedGame: ...

    def start(
        self,
        id: uuid.UUID,
        *,
        map: entities.Map,
        conquistator_location: entities.HexCoordinate,
    ) -> None: ...


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

    proposed = repository.add_player(game_id=game_id, username=username)
    if proposed.max_players == len(proposed.players):
        map = generate_map()
        deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
        repository.start(
            game_id,
            map=map,
            conquistator_location=random.choice(deserts).coordinate,
        )
    return proposed
