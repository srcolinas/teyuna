import collections
import dataclasses
import itertools
import random
from collections.abc import Mapping
from enum import Enum
from typing import Final, Self, Sequence, NamedTuple

from .. import player

MAX_TERRACES: Final[int] = 5
MAX_PATHS: Final[int] = 15
MAX_GREAT_TERRACES: Final[int] = 4


class HexType(str, Enum):
    """Types of hex tiles on the board."""

    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class HexCoordinate(NamedTuple):
    """Axial coordinate for hex grid positioning.

    Uses the axial coordinate system (q, r) which is standard for hex grids.
    See: https://www.redblobgames.com/grids/hexagons/.
    """

    q: int
    r: int


class VertexCoordinate(NamedTuple):
    """Coordinate for a vertex (corner) of a hex.

    A vertex is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top vertex, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: int


class EdgeCoordinate(NamedTuple):
    """Coordinate for an edge (side) of a hex.

    An edge is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top-right edge, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: int


class Hex(NamedTuple):
    """A hex tile on the game board."""

    coordinate: HexCoordinate
    type: HexType
    number: int


type Map = list[Hex]


class ResourceCard(str, Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


class WisdomCard(str, Enum):
    WARRIOR = "warrior"
    BLESSING_OF_ALUNA = "blessing of aluna"
    WINDOM_OF_MAMO = "wisdom of mamo"
    PATHFINDER = "pathfinder"
    LEGACY_OF_THE_ELDERS = "legacy of the elders"


class SettlementType(str, Enum):
    TERRACE = "terrace"
    GREAT_TERRACE = "great terrace"


@dataclasses.dataclass
class Player:
    cards: collections.Counter[WisdomCard]
    played_cards: collections.Counter[WisdomCard]
    resources: collections.Counter[ResourceCard]
    settlements: dict[VertexCoordinate, SettlementType]
    paths: set[EdgeCoordinate]


class InvalidSettlementLocation(Exception):
    pass


class InvalidPathLocation(Exception):
    pass


class PlayerNotInTurn(Exception):
    pass


@dataclasses.dataclass
class ActiveGame:
    map: Map
    players: Mapping[player.Nickname, Player]
    conquistator_location: HexCoordinate
    turn_order: tuple[player.Nickname, ...]

    _available_settlement_locations: set[tuple[int, int, int]] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )
    _available_path_locations: set[tuple[int, int, int]] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._available_settlement_locations = set()
        self._available_path_locations = set()
        for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if item not in _INVALID_HEX_COORDINATES:
                self._available_settlement_locations.add(item)
                self._available_path_locations.add(item)

    @classmethod
    def create_new(cls, players: Sequence[player.Nickname]) -> Self:
        map = _generate_map()
        deserts = [hex for hex in map if hex.type == HexType.DESERT]
        players = list(players)
        random.shuffle(players)
        return cls(
            map=map,
            conquistator_location=random.choice(deserts).coordinate,
            turn_order=tuple(players),
            players={
                nickname: Player(
                    cards=collections.Counter(),
                    played_cards=collections.Counter(),
                    resources=collections.Counter(),
                    settlements=dict(),
                    paths=set(),
                )
                for nickname in players
            },
        )

    def add_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        if to != self.turn_order[0]:
            raise PlayerNotInTurn

        desired = (q, r, direction)
        if desired not in self._available_settlement_locations:
            raise InvalidSettlementLocation

        dq5, dr5 = _NEIGHBOR[(direction + 5) % 6]
        blocked_vertices = [
            (q, r, direction),  # self
            (q, r, (direction + 1) % 6),  # adjacent on same hex (clockwise)
            (q, r, (direction + 5) % 6),  # adjacent on same hex (counterclockwise)
            (
                q + dq5,
                r + dr5,
                (direction + 1) % 6,
            ),  # adjacent across edge (counterclockwise)
        ]
        affected = set()
        for vq, vr, vd in blocked_vertices:
            affected.add((vq, vr, vd))
            aliases = _vertex_aliases(vq, vr, vd)
            affected.update(aliases)

        self._available_settlement_locations.difference_update(affected)

        self.players[to].settlements[
            VertexCoordinate(hex_coord=HexCoordinate(q=q, r=r), direction=direction)
        ] = SettlementType.TERRACE

    def add_path(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        if to != self.turn_order[0]:
            raise PlayerNotInTurn

        desired = (q, r, direction)
        if desired not in self._available_path_locations:
            raise InvalidPathLocation

        dq, dr = _NEIGHBOR[direction]
        alias = (q + dq, r + dr, (direction + 3) % 6)
        self._available_path_locations.difference_update([alias, desired])

        path = EdgeCoordinate(hex_coord=HexCoordinate(q=q, r=r), direction=direction)
        self.players[to].paths.add(path)


def _vertex_aliases(q: int, r: int, d: int) -> set[tuple[int, int, int]]:
    dq, dr = _NEIGHBOR[d]
    dq5, dr5 = _NEIGHBOR[(d + 5) % 6]
    return {
        (q + dq, r + dr, (d + 4) % 6),
        (q + dq5, r + dr5, (d + 2) % 6),
    }


def _generate_map() -> Map:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    map = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in _INVALID_HEX_COORDINATES:
                continue
            type_idx += 1
            coord = HexCoordinate(q=q, r=r)
            type = _TYPES[type_idx]
            if type is HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = _NUMBERS[number_idx]
            map.append(
                Hex(
                    coordinate=coord,
                    type=type,
                    number=number,
                )
            )

    return map


_TYPES = (
    [HexType.MOUNTAINS] * 3
    + [HexType.QUARRIES] * 3
    + [HexType.HIGHLANDS] * 4
    + [HexType.VALLEYS] * 4
    + [HexType.JUNGLE] * 4
    + [HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2

_INVALID_HEX_COORDINATES: Final[set[tuple[int, int]]] = {
    (-2, -2),
    (-2, -1),
    (-1, -2),
    (1, 2),
    (2, 1),
    (2, 2),
}

_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]
