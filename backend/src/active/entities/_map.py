from enum import Enum
from typing import Final, NamedTuple


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


class HexType(str, Enum):
    """Types of hex tiles on the board."""

    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class Coordinate(NamedTuple):
    """Coordinate for a vertex (corner) or edge of a hex.

    A vertex or edge is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top vertex, going clockwise.
    """

    q: int
    r: int
    d: int


class Hex(NamedTuple):
    """A hex tile on the game board."""

    q: int
    r: int
    type: HexType
    number: int


type Map = tuple[Hex, ...]


def canonical_vertex(q: int, r: int, d: int) -> Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(Coordinate(q=q, r=r, d=d))
    return min(aliases)


def vertex_aliases(q: int, r: int, d: int) -> set[Coordinate]:
    dq, dr = NEIGHBOR[d]
    dq5, dr5 = NEIGHBOR[(d + 5) % 6]
    return {
        Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_edge(q: int, r: int, d: int) -> Coordinate:
    alias = edge_alias(q, r, d)
    return min(alias, Coordinate(q=q, r=r, d=d))


def edge_alias(q: int, r: int, d: int) -> Coordinate:
    dq, dr = NEIGHBOR[d]
    return Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)
