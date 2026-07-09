import collections
import dataclasses
import itertools
import random
from collections.abc import ItemsView, Mapping, ValuesView
from enum import Enum
from typing import Final, Sequence, NamedTuple

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
class SettlementsCollection:
    _locations: dict[Coordinate, SettlementType] = dataclasses.field(
        default_factory=dict
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


Settlements = SettlementsCollection


class Player:
    def __init__(
        self,
        *,
        cards: collections.Counter[WisdomCard] | None = None,
        played_cards: collections.Counter[WisdomCard] | None = None,
        resources: collections.Counter[ResourceCard] | None = None,
        settlements: SettlementsCollection | None = None,
        paths: set[Coordinate] | None = None,
    ) -> None:
        self._cards = cards if cards is not None else collections.Counter()
        self._played_cards = (
            played_cards if played_cards is not None else collections.Counter()
        )
        self._resources = resources if resources is not None else collections.Counter()
        self._settlements = (
            settlements if settlements is not None else SettlementsCollection()
        )
        self._paths = paths if paths is not None else set()

    @property
    def cards(self) -> collections.Counter[WisdomCard]:
        return self._cards

    @property
    def played_cards(self) -> collections.Counter[WisdomCard]:
        return self._played_cards

    @property
    def resources(self) -> collections.Counter[ResourceCard]:
        return self._resources

    @property
    def settlements(self) -> SettlementsCollection:
        return self._settlements

    @property
    def paths(self) -> set[Coordinate]:
        return self._paths


class GamePhase(str, Enum):
    INITIAL = "initial"
    MAIN = "main"
    FINISHED = "finished"


class ActiveGame:
    def __init__(
        self,
        map: Sequence[Hex],
        players: Mapping[player.Nickname, Player],
        conquistator_location: Hex,
        turn_order: Sequence[player.Nickname],
        *,
        phase: GamePhase = GamePhase.INITIAL,
        rnd: random.Random | None = None,
    ) -> None:
        from . import _map

        self._map = tuple(map)
        self._players = dict(players)
        self._conquistator_location = conquistator_location
        self._turn_order = tuple(turn_order)
        self._phase = phase
        self._rnd = rnd if rnd is not None else random.Random()
        self._restricted_verticies: set[Coordinate] = set()
        self._free_verticies: set[Coordinate] = set()
        self._free_edges: set[Coordinate] = set()
        for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if item not in _map.INVALID_HEX_COORDINATES:
                vertex = _map.canonical_vertex(*item)
                self._free_verticies.add(vertex)

                edge = _map.canonical_edge(*item)
                self._free_edges.add(edge)

    @property
    def phase(self) -> GamePhase:
        return self._phase

    @property
    def players(self) -> Mapping[player.Nickname, Player]:
        return self._players

    @property
    def turn_order(self) -> tuple[player.Nickname, ...]:
        return self._turn_order

    @property
    def map(self) -> Map:
        return list(self._map)

    @property
    def conquistator_location(self) -> Hex:
        return self._conquistator_location

    @property
    def free_verticies(self) -> set[Coordinate]:
        return self._free_verticies

    @property
    def free_edges(self) -> set[Coordinate]:
        return self._free_edges

    @property
    def restricted_verticies(self) -> set[Coordinate]:
        return self._restricted_verticies

    def add_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        from . import _map

        target = _map.canonical_vertex(q, r, direction)
        self._players[to]._settlements[target] = SettlementType.TERRACE
        self._free_verticies.remove(target)
        dq5, dr5 = _map.NEIGHBOR[(direction + 5) % 6]
        blocked_vertices = [
            (q, r, (direction + 1) % 6),
            (q, r, (direction + 5) % 6),
            (q + dq5, r + dr5, (direction + 1) % 6),
        ]
        for vq, vr, vd in blocked_vertices:
            vertex = _map.canonical_vertex(vq, vr, vd)
            self._restricted_verticies.add(vertex)

    def add_path(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        from . import _map

        target = _map.canonical_edge(q, r, direction)
        self._free_edges.remove(target)
        self._players[to]._paths.add(target)

    def upgrade_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        from . import _map

        coord = _map.canonical_vertex(q, r, direction)
        self._players[to]._settlements[coord] = SettlementType.GREAT_TERRACE

    def discount_resources(
        self, to: player.Nickname, /, *, resources: collections.Counter[ResourceCard]
    ) -> None:
        self._players[to]._resources -= resources

    def grant_resources(
        self, to: player.Nickname, /, *, resources: collections.Counter[ResourceCard]
    ) -> None:
        self._players[to]._resources += resources
