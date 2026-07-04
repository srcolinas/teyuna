import collections
import random
import uuid
from collections.abc import Sequence
from typing import Protocol

from .. import _entities


class ManagedGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> _entities.ActiveGame | None: ...

    def add(self, game: _entities.ActiveGame) -> uuid.UUID: ...


class GameManager:
    def __init__(self, repository: ManagedGameRepository) -> None:
        self._repository = repository

    def start(
        self,
        players: Sequence[_entities.Username],
    ) -> uuid.UUID:
        map = _generate_map()
        deserts = [hex for hex in map if hex.type == _entities.HexType.DESERT]
        game = _entities.ActiveGame(
            map=map,
            conquistator_location=random.choice(deserts).coordinate,
            players={
                username: _entities.Player(
                    cards=collections.Counter(),
                    played_cards=collections.Counter(),
                    resources=collections.Counter(),
                    settlements=[],
                    paths=[],
                )
                for username in players
            },
        )
        return self._repository.add(game)


def _generate_map() -> _entities.Map:
    types = (
        [_entities.HexType.MOUNTAINS] * 3
        + [_entities.HexType.QUARRIES] * 3
        + [_entities.HexType.HIGHLANDS] * 4
        + [_entities.HexType.VALLEYS] * 4
        + [_entities.HexType.JUNGLE] * 4
        + [_entities.HexType.DESERT]
    )
    random.shuffle(types)

    numbers = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
    random.shuffle(numbers)

    map = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            try:
                coord = _entities.HexCoordinate(q=q, r=r)
            except ValueError:
                continue
            type = types.pop()
            number = 7 if type is _entities.HexType.DESERT else numbers.pop()
            map.append(
                _entities.Hex(
                    coordinate=coord,
                    type=type,
                    number=number,
                )
            )

    return map
