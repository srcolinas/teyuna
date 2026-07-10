import collections
import itertools
import random

from collections.abc import Sequence

from ... import player
from .. import entities
from . import _map


def create_new(players: Sequence[player.Nickname]) -> entities.ActiveGame:
    map = _generate_map()
    deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
    players = list(players)
    random.shuffle(players)
    free_verticies, free_edges = _initial_buildable_locations()
    return entities.ActiveGame(
        map=map,
        conquistator_location=random.choice(deserts),
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
        free_verticies=free_verticies,
        free_edges=free_edges,
    )


def _initial_buildable_locations() -> tuple[
    set[entities.Coordinate], set[entities.Coordinate]
]:
    free_verticies: set[entities.Coordinate] = set()
    free_edges: set[entities.Coordinate] = set()
    for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if item not in entities.INVALID_HEX_COORDINATES:
            free_verticies.add(_map.canonical_vertex(*item))
            free_edges.add(_map.canonical_edge(*item))
    return free_verticies, free_edges


def _generate_map() -> tuple[entities.Hex, ...]:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    map = []
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
            map.append(
                entities.Hex(
                    q=q,
                    r=r,
                    type=type,
                    number=number,
                )
            )

    return tuple(map)


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
