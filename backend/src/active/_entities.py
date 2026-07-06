import collections
import dataclasses
import itertools
from collections.abc import Mapping
from enum import Enum
from typing import Annotated, Final, Self

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
    settlements: list[Settlement]
    paths: list[EdgeCoordinate]


class InvalidSettlementLocation(Exception):
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

    def __post_init__(self) -> None:
        self._available_settlement_locations = {
            (q, r, d)
            for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6))
            if (q, r) not in {(-2, -2), (-2, -1), (-1, -2), (1, 2), (2, 1), (2, 2)}
        }

    def add_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> Settlement:
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
        self.players[to].settlements.append(settlement)
        return settlement


def _vertex_aliases(q: int, r: int, d: int) -> set[tuple[int, int, int]]:
    dq, dr = _NEIGHBOR[d]
    dq5, dr5 = _NEIGHBOR[(d + 5) % 6]
    return {
        (q + dq, r + dr, (d + 4) % 6),
        (q + dq5, r + dr5, (d + 2) % 6),
    }
