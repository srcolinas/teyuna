import collections
import dataclasses
import itertools
import random
from collections.abc import ItemsView, Mapping, ValuesView
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
class Settlements:
    _locations: dict[Coordinate, SettlementType] = dataclasses.field(
        default_factory=dict
    )
    _counts: collections.Counter[SettlementType] = dataclasses.field(
        default_factory=collections.Counter, init=False, repr=False
    )

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


@dataclasses.dataclass
class Player:
    cards: collections.Counter[WisdomCard] = dataclasses.field(
        default_factory=collections.Counter
    )
    played_cards: collections.Counter[WisdomCard] = dataclasses.field(
        default_factory=collections.Counter
    )
    resources: collections.Counter[ResourceCard] = dataclasses.field(
        default_factory=collections.Counter
    )
    settlements: Settlements = dataclasses.field(default_factory=Settlements)
    paths: set[Coordinate] = dataclasses.field(default_factory=set)


class GamePhase(str, Enum):
    INITIAL = "initial"
    MAIN = "main"
    FINISHED = "finished"


class InvalidSettlementLocation(Exception):
    pass


class InvalidPathLocation(Exception):
    pass


class PlayerNotInTurn(Exception):
    pass


class InsufficientResources(Exception):
    pass


class InvalidGamePhase(Exception):
    pass


@dataclasses.dataclass
class ActiveGame:
    map: Map
    players: Mapping[player.Nickname, Player]
    conquistator_location: Hex
    turn_order: tuple[player.Nickname, ...]
    phase: GamePhase = GamePhase.INITIAL

    _free_verticies: set[tuple[int, int, int]] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )
    _restricted_verticies: set[tuple[int, int, int]] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )
    _free_edges: set[tuple[int, int, int]] = dataclasses.field(
        default_factory=set, init=False, repr=False
    )
    _rnd: random.Random = dataclasses.field(default_factory=random.Random, init=True)

    def __post_init__(self) -> None:
        if self._rnd is None:
            self._rnd = random.Random()
        self._restricted_verticies = set()
        self._free_verticies = set()
        self._free_edges = set()
        for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if item not in _INVALID_HEX_COORDINATES:
                vertex = _canonical_vertex(*item)
                self._free_verticies.add(vertex)

                edge = _canonical_edge(*item)
                self._free_edges.add(edge)

    @classmethod
    def create_new(cls, players: Sequence[player.Nickname]) -> Self:
        map = _generate_map()
        deserts = [hex for hex in map if hex.type == HexType.DESERT]
        players = list(players)
        random.shuffle(players)
        return cls(
            map=map,
            conquistator_location=random.choice(deserts),
            turn_order=tuple(players),
            players={
                nickname: Player(
                    cards=collections.Counter(),
                    played_cards=collections.Counter(),
                    resources=collections.Counter(),
                    settlements=Settlements(),
                    paths=set(),
                )
                for nickname in players
            },
        )

    def add_initial_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        if self.phase is not GamePhase.INITIAL:
            raise InvalidGamePhase

        if to != self.turn_order[0]:
            raise PlayerNotInTurn

        target = _canonical_vertex(q, r, direction)
        if target not in self._free_verticies or target in self._restricted_verticies:
            raise InvalidSettlementLocation

        self._free_verticies.remove(target)

        dq5, dr5 = _NEIGHBOR[(direction + 5) % 6]
        blocked_vertices = [
            (q, r, (direction + 1) % 6),  # adjacent on same hex (clockwise)
            (q, r, (direction + 5) % 6),  # adjacent on same hex (counterclockwise)
            (
                q + dq5,
                r + dr5,
                (direction + 1) % 6,
            ),  # adjacent across edge
        ]
        for vq, vr, vd in blocked_vertices:
            vertex = _canonical_vertex(vq, vr, vd)
            self._restricted_verticies.add(vertex)

        self.players[to].settlements[target] = SettlementType.TERRACE

    def _add_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        paths = self.players[to].paths
        dq5, dr5 = _NEIGHBOR[(direction + 5) % 6]
        adjacent_edges = (
            _canonical_edge(q, r, (direction + 5) % 6),
            _canonical_edge(q, r, direction),
            _canonical_edge(q + dq5, r + dr5, (direction + 1) % 6),
        )
        if not any(edge in paths for edge in adjacent_edges):
            raise InvalidSettlementLocation

        self.add_initial_terrace(to, q=q, r=r, direction=direction)

    def _add_path(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        if to != self.turn_order[0]:
            raise PlayerNotInTurn

        if len(self.players[to].paths) >= MAX_PATHS:
            raise InsufficientResources

        target = _canonical_edge(q, r, direction)
        if target not in self._free_edges:
            raise InvalidPathLocation

        this_player = self.players[to]
        settlements = this_player.settlements
        paths = this_player.paths
        free_verticies = self._free_verticies

        forbidden = True
        q, r, direction = target
        vertices = [
            _canonical_vertex(q, r, direction),
            _canonical_vertex(q, r, (direction + 1) % 6),
        ]
        for v in vertices:
            if v in settlements:
                forbidden = False
                break
            if v in free_verticies:
                vq, vr, vd = v
                dq5, dr5 = _NEIGHBOR[(vd + 5) % 6]
                for e in (
                    _canonical_edge(vq, vr, (vd + 5) % 6),
                    _canonical_edge(vq, vr, vd),
                    _canonical_edge(vq + dq5, vr + dr5, (vd + 1) % 6),
                ):
                    if e != target and e in paths:
                        forbidden = False
                        break

        if forbidden:
            raise InvalidPathLocation

        self._free_edges.remove(target)
        self.players[to].paths.add(target)

    def buy_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        resources = self.players[to].resources
        if resources[ResourceCard.STONE] < 1:
            raise InsufficientResources

        if resources[ResourceCard.WOOD] < 1:
            raise InsufficientResources

        if resources[ResourceCard.COTTON] < 1:
            raise InsufficientResources

        if resources[ResourceCard.MAIZE] < 1:
            raise InsufficientResources

        if self.players[to].settlements.count(SettlementType.TERRACE) >= MAX_TERRACES:
            raise InsufficientResources

        self._add_terrace(to, q=q, r=r, direction=direction)
        resources[ResourceCard.STONE] -= 1
        resources[ResourceCard.WOOD] -= 1
        resources[ResourceCard.COTTON] -= 1
        resources[ResourceCard.MAIZE] -= 1

    def buy_path(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        resources = self.players[to].resources
        if resources[ResourceCard.STONE] < 1:
            raise InsufficientResources

        if resources[ResourceCard.WOOD] < 1:
            raise InsufficientResources

        self._add_path(to, q=q, r=r, direction=direction)
        resources[ResourceCard.STONE] -= 1
        resources[ResourceCard.WOOD] -= 1

    def buy_great_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        if to != self.turn_order[0]:
            raise PlayerNotInTurn

        resources = self.players[to].resources
        if resources[ResourceCard.GOLD] < 3:
            raise InsufficientResources
        if resources[ResourceCard.MAIZE] < 2:
            raise InsufficientResources

        if (
            self.players[to].settlements.count(SettlementType.GREAT_TERRACE)
            >= MAX_GREAT_TERRACES
        ):
            raise InsufficientResources

        coord = _canonical_vertex(q, r, direction)
        if (
            coord not in self.players[to].settlements
            or self.players[to].settlements[coord] is not SettlementType.TERRACE
        ):
            raise InvalidSettlementLocation(
                "You must first build a terrace at specified location."
            )

        self.players[to].settlements[coord] = SettlementType.GREAT_TERRACE

        resources[ResourceCard.GOLD] -= 3
        resources[ResourceCard.MAIZE] -= 2

    def produce(self) -> None:
        if self.phase is not GamePhase.MAIN:
            raise InvalidGamePhase

        # TODO: improve performance by using a differnet data structure
        # to represent the map and figure out which players benefit
        # from the production roll more efficiently.
        roll_1, roll_2 = self._rnd.randint(1, 6), self._rnd.randint(1, 6)
        total = roll_1 + roll_2
        for hex in self.map:
            if hex.number == total:
                if hex.type is not HexType.DESERT:
                    resource = _HEX_TYPE_TO_RESOURCE[hex.type]
                    for p in self.turn_order:
                        settlements = self.players[p].settlements
                        for i in range(6):
                            coord = _canonical_vertex(hex.q, hex.r, i)
                            if coord not in settlements:
                                continue
                            if settlements[coord] is SettlementType.TERRACE:
                                self.players[p].resources[resource] += 1
                            elif settlements[coord] is SettlementType.GREAT_TERRACE:
                                self.players[p].resources[resource] += 2


def _canonical_vertex(q: int, r: int, d: int) -> Coordinate:
    aliases = _vertex_aliases(q, r, d)
    aliases.add(Coordinate(q=q, r=r, d=d))
    return min(aliases)


def _vertex_aliases(q: int, r: int, d: int) -> set[Coordinate]:
    dq, dr = _NEIGHBOR[d]
    dq5, dr5 = _NEIGHBOR[(d + 5) % 6]
    return {
        Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def _canonical_edge(q: int, r: int, d: int) -> Coordinate:
    alias = _edge_alias(q, r, d)
    return min(alias, Coordinate(q=q, r=r, d=d))


def _edge_alias(q: int, r: int, d: int) -> Coordinate:
    dq, dr = _NEIGHBOR[d]
    return Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


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
            type = _TYPES[type_idx]
            if type is HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = _NUMBERS[number_idx]
            map.append(
                Hex(
                    q=q,
                    r=r,
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

_HEX_TYPE_TO_RESOURCE: Final[dict[HexType, ResourceCard]] = {
    HexType.MOUNTAINS: ResourceCard.GOLD,
    HexType.QUARRIES: ResourceCard.STONE,
    HexType.HIGHLANDS: ResourceCard.COTTON,
    HexType.VALLEYS: ResourceCard.MAIZE,
    HexType.JUNGLE: ResourceCard.WOOD,
}
