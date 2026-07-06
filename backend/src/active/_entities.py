import collections
import dataclasses
import itertools
import random
from collections.abc import Mapping
from enum import Enum
from typing import Annotated, Final, Self, Sequence

import pydantic

from .. import player


class HexType(str, Enum):
    """Types of hex tiles on the board."""

    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class HexCoordinate(pydantic.BaseModel):
    """Axial coordinate for hex grid positioning.

    Uses the axial coordinate system (q, r) which is standard for hex grids.
    See: https://www.redblobgames.com/grids/hexagons/.
    """

    q: Annotated[
        int,
        pydantic.Field(
            ge=-2,
            le=2,
            description="0 along the top left to bottom right diagonal of the board, positives to the right",
        ),
    ]
    r: Annotated[
        int,
        pydantic.Field(
            ge=-2,
            le=2,
            description="0 along the horizontal axes of the board, positives to the bottom",
        ),
    ]

    model_config = pydantic.ConfigDict(frozen=True)

    @pydantic.model_validator(mode="after")
    def check_hex_is_valid(self) -> Self:
        if (self.q, self.r) in {(-2, -2), (-2, -1), (-1, -2), (1, 2), (2, 1), (2, 2)}:
            raise ValueError("Hex coordinate is invalid")
        return self


class VertexCoordinate(pydantic.BaseModel):
    """Coordinate for a vertex (corner) of a hex.

    A vertex is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top vertex, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class EdgeCoordinate(pydantic.BaseModel):
    """Coordinate for an edge (side) of a hex.

    An edge is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top-right edge, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class Hex(pydantic.BaseModel):
    """A hex tile on the game board."""

    coordinate: HexCoordinate
    type: HexType
    number: Annotated[int, pydantic.Field(default=None, ge=2, le=12)]

    model_config = pydantic.ConfigDict(frozen=True)


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


class Settlement(pydantic.BaseModel):
    location: VertexCoordinate
    type: SettlementType


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


_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]


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
        invalid = {(-2, -2), (-2, -1), (-1, -2), (1, 2), (2, 1), (2, 2)}
        self._available_settlement_locations = set()
        self._available_path_locations = set()
        for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if item not in invalid:
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
    ) -> Settlement:
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

        settlement = Settlement(
            location=VertexCoordinate(
                hex_coord=HexCoordinate(q=q, r=r), direction=direction
            ),
            type=SettlementType.TERRACE,
        )
        self.players[to].settlements[settlement.location] = settlement.type
        return settlement

    def add_path(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> EdgeCoordinate:
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
        return path


def _vertex_aliases(q: int, r: int, d: int) -> set[tuple[int, int, int]]:
    dq, dr = _NEIGHBOR[d]
    dq5, dr5 = _NEIGHBOR[(d + 5) % 6]
    return {
        (q + dq, r + dr, (d + 4) % 6),
        (q + dq5, r + dr5, (d + 2) % 6),
    }


def _generate_map() -> Map:
    types = (
        [HexType.MOUNTAINS] * 3
        + [HexType.QUARRIES] * 3
        + [HexType.HIGHLANDS] * 4
        + [HexType.VALLEYS] * 4
        + [HexType.JUNGLE] * 4
        + [HexType.DESERT]
    )
    random.shuffle(types)

    numbers = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
    random.shuffle(numbers)

    map = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            try:
                coord = HexCoordinate(q=q, r=r)
            except ValueError:
                continue
            type = types.pop()
            number = 7 if type is HexType.DESERT else numbers.pop()
            map.append(
                Hex(
                    coordinate=coord,
                    type=type,
                    number=number,
                )
            )

    return map
