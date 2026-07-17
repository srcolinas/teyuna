import collections
import random
import uuid

from collections.abc import Sequence
from typing import Protocol

from ... import player
from .. import entities


class CreateGameRepository(Protocol):
    def add(self, game: entities.ActiveGame) -> uuid.UUID: ...


def create_game(
    repository: CreateGameRepository,
    players: Sequence[player.Nickname],
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
        wisdom_deck=_create_wisdom_deck(),
    )
    return repository.add(game)


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


def _create_wisdom_deck() -> list[entities.WisdomCard]:
    deck = (
        [entities.WisdomCard.WARRIOR] * 14
        + [entities.WisdomCard.LEGACY_OF_THE_ELDERS] * 5
        + [entities.WisdomCard.PATHFINDER] * 2
        + [entities.WisdomCard.BLESSING_OF_ALUNA] * 2
        + [entities.WisdomCard.WINDOM_OF_MAMO] * 2
    )
    random.shuffle(deck)
    return deck


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
