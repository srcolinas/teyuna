import collections
import dataclasses
import itertools
from collections.abc import ItemsView, Mapping, ValuesView
from enum import Enum
from typing import Final, Sequence, NamedTuple

from ... import player
from . import _map

MAX_TERRACES: Final[int] = 5
MAX_PATHS: Final[int] = 15
MAX_GREAT_TERRACES: Final[int] = 4


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
    _locations: dict[_map.Coordinate, SettlementType] = dataclasses.field(
        default_factory=dict
    )
    _counts: collections.Counter[SettlementType] = dataclasses.field(
        default_factory=collections.Counter, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._counts = collections.Counter(self._locations.values())

    def __contains__(self, coord: _map.Coordinate) -> bool:
        return coord in self._locations

    def __getitem__(self, coord: _map.Coordinate) -> SettlementType:
        return self._locations[coord]

    def __setitem__(self, coord: _map.Coordinate, type: SettlementType) -> None:
        if coord in self._locations:
            self._counts[self._locations[coord]] -= 1
        self._locations[coord] = type
        self._counts[type] += 1

    def items(self) -> ItemsView[_map.Coordinate, SettlementType]:
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


class Player:
    def __init__(
        self,
        *,
        cards: CardCount | None = None,
        played_cards: CardCount | None = None,
        resources: ResourceCount | None = None,
        settlements: SettlementsCollection | None = None,
        paths: set[_map.Coordinate] | None = None,
    ) -> None:
        self._cards = cards if cards is not None else collections.Counter()
        self._played_cards = (
            played_cards if played_cards is not None else collections.Counter()
        )
        self._resources = (
            resources
            if resources is not None
            else collections.Counter(
                {
                    ResourceCard.GOLD: 0,
                    ResourceCard.STONE: 0,
                    ResourceCard.COTTON: 0,
                    ResourceCard.MAIZE: 0,
                    ResourceCard.WOOD: 0,
                }
            )
        )
        self._settlements = (
            settlements if settlements is not None else SettlementsCollection()
        )
        self._paths = paths if paths is not None else set()
        self._resource_supply = collections.Counter(
            {
                ResourceCard.GOLD: 4,
                ResourceCard.STONE: 4,
                ResourceCard.COTTON: 4,
                ResourceCard.MAIZE: 4,
                ResourceCard.WOOD: 4,
            }
        )

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
    def paths(self) -> set[_map.Coordinate]:
        return self._paths


class GamePhase(str, Enum):
    INITIAL = "initial"
    MAIN = "main"
    FINISHED = "finished"


class TradeProposal(NamedTuple):
    offer: ResourceCount
    request: ResourceCount


class ActiveGame:
    def __init__(
        self,
        map: Sequence[_map.Hex],
        players: Mapping[player.Nickname, Player],
        conquistator_location: _map.Hex,
        turn_order: Sequence[player.Nickname],
        *,
        phase: GamePhase = GamePhase.INITIAL,
    ) -> None:
        from . import _map

        self._map = tuple(map)
        self._players = dict(players)
        self._conquistator_location = conquistator_location
        self._turn_order = tuple(turn_order)
        self._phase = phase
        self._resource_supply = collections.Counter(
            {
                ResourceCard.GOLD: 19,
                ResourceCard.STONE: 19,
                ResourceCard.COTTON: 19,
                ResourceCard.MAIZE: 19,
                ResourceCard.WOOD: 19,
            }
        )
        self._trade_proposals: dict[player.Nickname, TradeProposal] = {}
        self._restricted_verticies: set[_map.Coordinate] = set()
        self._free_verticies: set[_map.Coordinate] = set()
        self._free_edges: set[_map.Coordinate] = set()
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
    def map(self) -> _map.Map:
        return self._map

    @property
    def conquistator_location(self) -> _map.Hex:
        return self._conquistator_location

    @property
    def free_verticies(self) -> set[_map.Coordinate]:
        return self._free_verticies

    @property
    def free_edges(self) -> set[_map.Coordinate]:
        return self._free_edges

    @property
    def restricted_verticies(self) -> set[_map.Coordinate]:
        return self._restricted_verticies

    @property
    def trade_proposals(self) -> dict[player.Nickname, TradeProposal]:
        return self._trade_proposals

    @property
    def resource_supply(self) -> ResourceCount:
        return self._resource_supply

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
        target = _map.canonical_edge(q, r, direction)
        self._free_edges.remove(target)
        self._players[to]._paths.add(target)

    def upgrade_terrace(
        self, to: player.Nickname, /, *, q: int, r: int, direction: int
    ) -> None:
        coord = _map.canonical_vertex(q, r, direction)
        self._players[to]._settlements[coord] = SettlementType.GREAT_TERRACE

    def discount_resources(
        self, to: player.Nickname, /, *, resources: collections.Counter[ResourceCard]
    ) -> None:
        self._players[to]._resources -= resources
        self._resource_supply += resources

    def grant_resources(
        self, to: player.Nickname, /, *, resources: collections.Counter[ResourceCard]
    ) -> None:
        self._players[to]._resources += resources
        self._resource_supply -= resources

    def add_trade_proposal(
        self, by: player.Nickname, /, *, offer: ResourceCount, request: ResourceCount
    ) -> None:
        self._trade_proposals[by] = TradeProposal(offer, request)
