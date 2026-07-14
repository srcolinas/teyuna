import collections
import dataclasses
import uuid
from collections.abc import ItemsView, ValuesView
from enum import Enum
from typing import Final, NamedTuple

from .. import player

MAX_TERRACES: Final[int] = 5
MAX_PATHS: Final[int] = 15
MAX_GREAT_TERRACES: Final[int] = 4


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


def canonical_vertex(q: int, r: int, d: int) -> Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(Coordinate(q=q, r=r, d=d))
    return min(aliases)


def vertex_aliases(q: int, r: int, d: int) -> set[Coordinate]:
    dq, dr = delta_to_neighbor(d)
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    return {
        Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_edge(q: int, r: int, d: int) -> Coordinate:
    alias = edge_alias(q, r, d)
    return min(alias, Coordinate(q=q, r=r, d=d))


def edge_alias(q: int, r: int, d: int) -> Coordinate:
    dq, dr = delta_to_neighbor(d)
    return Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


def delta_to_neighbor(d: int) -> tuple[int, int]:
    dq, dr = _NEIGHBOR[d]
    return dq, dr


_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]


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


HARBOUR_LOCATIONS: Final[dict[Coordinate, ResourceCard | None]] = {
    canonical_vertex(-1, -1, 4): ResourceCard.WOOD,
    canonical_vertex(-1, -1, 5): ResourceCard.WOOD,
    canonical_vertex(0, -2, 0): None,
    canonical_vertex(0, -2, 5): None,
    canonical_vertex(1, -2, 0): ResourceCard.MAIZE,
    canonical_vertex(1, -2, 1): ResourceCard.MAIZE,
    canonical_vertex(2, -1, 0): ResourceCard.STONE,
    canonical_vertex(2, -1, 1): ResourceCard.STONE,
    canonical_vertex(2, 0, 1): None,
    canonical_vertex(2, 0, 2): None,
    canonical_vertex(1, 1, 2): ResourceCard.COTTON,
    canonical_vertex(1, 1, 3): ResourceCard.COTTON,
    canonical_vertex(-1, 2, 2): None,
    canonical_vertex(-1, 2, 3): None,
    canonical_vertex(-2, 2, 3): None,
    canonical_vertex(-2, 2, 4): None,
    canonical_vertex(-2, 1, 4): ResourceCard.GOLD,
    canonical_vertex(-2, 1, 5): ResourceCard.GOLD,
}


@dataclasses.dataclass
class SettlementsCollection:
    _locations: dict[Coordinate, SettlementType] = dataclasses.field(
        default_factory=dict,
    )
    _counts: collections.Counter[SettlementType] = dataclasses.field(
        default_factory=collections.Counter, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._counts = collections.Counter(self._locations.values())

    def __contains__(self, coord: Coordinate) -> bool:
        return coord in self._locations

    def __getitem__(self, coord: Coordinate) -> SettlementType:
        return self._locations[coord]

    def __setitem__(self, coord: Coordinate, type: SettlementType) -> None:
        if coord in self._locations:
            self._counts[self._locations[coord]] -= 1
        self._locations[coord] = type
        self._counts[type] += 1

    def items(self) -> ItemsView[Coordinate, SettlementType]:
        return self._locations.items()

    def values(self) -> ValuesView[SettlementType]:
        return self._locations.values()

    def count(self, type: SettlementType) -> int:
        return self._counts[type]

    @property
    def counts(self) -> collections.Counter[SettlementType]:
        return collections.Counter(self._counts)


type CardCount = collections.Counter[WisdomCard]
type ResourceCount = collections.Counter[ResourceCard]


def _default_resources() -> ResourceCount:
    return collections.Counter(
        {
            ResourceCard.GOLD: 0,
            ResourceCard.STONE: 0,
            ResourceCard.COTTON: 0,
            ResourceCard.MAIZE: 0,
            ResourceCard.WOOD: 0,
        }
    )


@dataclasses.dataclass(kw_only=True)
class Player:
    cards: CardCount = dataclasses.field(default_factory=collections.Counter)
    played_cards: CardCount = dataclasses.field(default_factory=collections.Counter)
    resources: ResourceCount = dataclasses.field(default_factory=_default_resources)
    settlements: SettlementsCollection = dataclasses.field(
        default_factory=SettlementsCollection
    )
    paths: set[Coordinate] = dataclasses.field(default_factory=set)


class TradeProposal(NamedTuple):
    by: player.Nickname
    offer: ResourceCount
    request: ResourceCount


def _default_resource_supply() -> ResourceCount:
    return collections.Counter(
        {
            ResourceCard.GOLD: 19,
            ResourceCard.STONE: 19,
            ResourceCard.COTTON: 19,
            ResourceCard.MAIZE: 19,
            ResourceCard.WOOD: 19,
        }
    )


@dataclasses.dataclass(kw_only=True)
class ActiveGame:
    map: tuple[Hex, ...]
    players: dict[player.Nickname, Player]
    conquistator_location: Hex
    turn_order: tuple[player.Nickname, ...]
    player_idx: int = 0
    free_verticies: set[Coordinate] = dataclasses.field(default_factory=set)
    free_edges: set[Coordinate] = dataclasses.field(default_factory=set)
    resource_supply: ResourceCount = dataclasses.field(
        default_factory=_default_resource_supply
    )
    trade_proposals: dict[uuid.UUID, TradeProposal] = dataclasses.field(
        default_factory=dict
    )
    restricted_verticies: set[Coordinate] = dataclasses.field(default_factory=set)
    wisdom_deck: list[WisdomCard] = dataclasses.field(default_factory=list)

    @property
    def active_player(self) -> player.Nickname:
        return self.turn_order[self.player_idx]
