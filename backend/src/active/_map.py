import random
from typing import Final

from . import entities

NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]

INVALID_HEX_COORDINATES: Final[set[tuple[int, int]]] = {
    (-2, -2),
    (-2, -1),
    (-1, -2),
    (1, 2),
    (2, 1),
    (2, 2),
}


def canonical_vertex(q: int, r: int, d: int) -> entities.Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(entities.Coordinate(q=q, r=r, d=d))
    return min(aliases)


def vertex_aliases(q: int, r: int, d: int) -> set[entities.Coordinate]:
    dq, dr = NEIGHBOR[d]
    dq5, dr5 = NEIGHBOR[(d + 5) % 6]
    return {
        entities.Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        entities.Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_edge(q: int, r: int, d: int) -> entities.Coordinate:
    alias = edge_alias(q, r, d)
    return min(alias, entities.Coordinate(q=q, r=r, d=d))


def edge_alias(q: int, r: int, d: int) -> entities.Coordinate:
    dq, dr = NEIGHBOR[d]
    return entities.Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


def generate_map() -> entities.Map:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    map = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in INVALID_HEX_COORDINATES:
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
