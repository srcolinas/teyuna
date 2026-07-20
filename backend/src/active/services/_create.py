import collections
import datetime
import random
import uuid

from collections.abc import Sequence
from typing import Protocol

from ... import player
from .. import entities


class CreateGameRepository(Protocol):
    def add(
        self, game: entities.ActiveGame, *, phase_deadline: datetime.datetime | None
    ) -> uuid.UUID: ...


def create_game(
    repository: CreateGameRepository,
    players: Sequence[player.Nickname],
    *,
    first_placement_timeout: datetime.timedelta,
) -> uuid.UUID:
    map = generate_map()
    deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
    players = list(players)
    random.shuffle(players)
    desert = random.choice(deserts)
    game = entities.ActiveGame(
        map=map,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        turn_order=tuple(players),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in players
        },
    )
    now = datetime.datetime.now(datetime.UTC)
    phase_deadline = now + first_placement_timeout
    return repository.add(game, phase_deadline=phase_deadline)


def generate_map() -> tuple[entities.Hex, ...]:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    tiles = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in entities.INVALID_HEX_COORDINATES:
                continue
            type_idx += 1
            type = _TYPES[type_idx]
            if type is entities.HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = _NUMBERS[number_idx]
            tiles.append(
                entities.Hex(
                    q=q,
                    r=r,
                    type=type,
                    number=number,
                )
            )

    return tuple(tiles)


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
