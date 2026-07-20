import collections
import dataclasses
import itertools
import random
import uuid
from collections.abc import ItemsView, KeysView, Set, ValuesView
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


class HexLocation(NamedTuple):
    """A the coordintes of the hex, not including any vertex or edge."""

    q: int
    r: int


class Hex(NamedTuple):
    """A hex tile on the game board."""

    q: int
    r: int
    type: HexType
    number: int


def canonical_vertex(q: int, r: int, d: int) -> Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(Coordinate(q=q, r=r, d=d))
    return _canonical_among(aliases)


def vertex_aliases(q: int, r: int, d: int) -> set[Coordinate]:
    dq, dr = delta_to_neighbor(d)
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    return {
        Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_edge(q: int, r: int, d: int) -> Coordinate:
    return _canonical_among({edge_alias(q, r, d), Coordinate(q=q, r=r, d=d)})


def edge_alias(q: int, r: int, d: int) -> Coordinate:
    dq, dr = delta_to_neighbor(d)
    return Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


def delta_to_neighbor(d: int) -> tuple[int, int]:
    dq, dr = _NEIGHBOR[d]
    return dq, dr


def vertices_of_edge(edge: Coordinate) -> tuple[Coordinate, Coordinate]:
    q, r, d = edge
    return (
        canonical_vertex(q, r, d),
        canonical_vertex(q, r, (d + 1) % 6),
    )


def edges_adjacent_to_vertex(q: int, r: int, d: int) -> set[Coordinate]:
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    adjacent: set[Coordinate] = set()
    for edge_q, edge_r, edge_d in (
        (q, r, (d + 5) % 6),
        (q, r, d),
        (q + dq5, r + dr5, (d + 1) % 6),
    ):
        try:
            adjacent.add(canonical_edge(edge_q, edge_r, edge_d))
        except ValueError:
            # Edge lies only between off-board / invalid hexes.
            continue
    return adjacent


def hex_locations_at_vertex(q: int, r: int, d: int) -> set[HexLocation]:
    """Return the valid board hexes that meet at the given vertex."""
    locs = {HexLocation(q=q, r=r)}
    for alias in vertex_aliases(q, r, d):
        locs.add(HexLocation(q=alias.q, r=alias.r))
    return {loc for loc in locs if _is_valid_hex(loc.q, loc.r)}


_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]


def _is_valid_hex(q: int, r: int) -> bool:
    return -2 <= q <= 2 and -2 <= r <= 2 and (q, r) not in INVALID_HEX_COORDINATES


def _canonical_among(candidates: set[Coordinate]) -> Coordinate:
    valid = {c for c in candidates if _is_valid_hex(c.q, c.r)}
    if not valid:
        raise ValueError("no valid board hex among coordinate aliases")
    return min(valid)


class ResourceCard(str, Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


HEX_TYPE_TO_RESOURCE: Final[dict[HexType, ResourceCard]] = {
    HexType.MOUNTAINS: ResourceCard.GOLD,
    HexType.QUARRIES: ResourceCard.STONE,
    HexType.HIGHLANDS: ResourceCard.COTTON,
    HexType.VALLEYS: ResourceCard.MAIZE,
    HexType.JUNGLE: ResourceCard.WOOD,
}


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

    def locations(self) -> KeysView[Coordinate]:
        return self._locations.keys()

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
    cards_bought_this_turn: CardCount = dataclasses.field(
        default_factory=collections.Counter
    )
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
    to: set[player.Nickname]


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


def _default_wisdom_deck() -> list[WisdomCard]:
    deck = (
        [WisdomCard.WARRIOR] * 14
        + [WisdomCard.LEGACY_OF_THE_ELDERS] * 5
        + [WisdomCard.PATHFINDER] * 2
        + [WisdomCard.BLESSING_OF_ALUNA] * 2
        + [WisdomCard.WINDOM_OF_MAMO] * 2
    )
    random.shuffle(deck)
    return deck


@dataclasses.dataclass(kw_only=True)
class ActiveGame:
    map: tuple[Hex, ...]
    players: dict[player.Nickname, Player]
    conquistator_location: HexLocation
    turn_order: tuple[player.Nickname, ...]
    player_idx: int = 0
    to_discard_resources: dict[player.Nickname, int] = dataclasses.field(
        default_factory=dict
    )
    resource_supply: ResourceCount = dataclasses.field(
        default_factory=_default_resource_supply
    )
    wisdom_deck: list[WisdomCard] = dataclasses.field(
        default_factory=_default_wisdom_deck
    )
    trade_proposals: dict[uuid.UUID, TradeProposal] = dataclasses.field(
        default_factory=dict
    )
    longest_road: tuple[player.Nickname | None, int] = dataclasses.field(
        default_factory=lambda: (None, 0)
    )
    biggest_army: tuple[player.Nickname | None, int] = dataclasses.field(
        default_factory=lambda: (None, 0)
    )
    _free_verticies: set[Coordinate] = dataclasses.field(init=False)
    _free_edges: set[Coordinate] = dataclasses.field(init=False)
    _restricted_verticies: set[Coordinate] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        free_verticies: set[Coordinate] = set()
        free_edges: set[Coordinate] = set()
        for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if (q, r) not in INVALID_HEX_COORDINATES:
                free_verticies.add(canonical_vertex(q, r, d))
                free_edges.add(canonical_edge(q, r, d))
        self._free_verticies = free_verticies
        self._free_edges = free_edges
        self._restricted_verticies = set()

    @property
    def active_player(self) -> player.Nickname:
        return self.turn_order[self.player_idx]

    @property
    def free_verticies(self) -> Set[Coordinate]:
        """
        Returns all vertices that don't have a settlement on them,
        even if they are adjacent to a settlement and can't be used
        to place a settlement.
        """
        return frozenset(self._free_verticies)

    @property
    def free_edges(self) -> Set[Coordinate]:
        """Returns all edges that don't have a path on them"""
        return frozenset(self._free_edges)

    @property
    def restricted_verticies(self) -> Set[Coordinate]:
        """
        Returns all free vertices that can't be used to place a settlement,
        but are adjacent to a settlement and therore can't be used to place
        a settlement. Any path should be able to go through these verticies
        though.
        """
        return frozenset(self._restricted_verticies)

    def use_vertex(
        self, by: player.Nickname, target: Coordinate, settlement: SettlementType
    ) -> None:
        dq5, dr5 = delta_to_neighbor((target.d + 5) % 6)
        blocked_vertices: set[Coordinate] = set()
        for vq, vr, vd in (
            (target.q, target.r, (target.d + 1) % 6),
            (target.q, target.r, (target.d + 5) % 6),
            (target.q + dq5, target.r + dr5, (target.d + 1) % 6),
        ):
            try:
                blocked_vertices.add(canonical_vertex(vq, vr, vd))
            except ValueError:
                # Adjacent corner lies only on off-board / invalid hexes.
                continue
        self._free_verticies.remove(target)
        self._restricted_verticies.update(blocked_vertices)
        self.players[by].settlements[target] = settlement

    def use_edge(self, by: player.Nickname, target: Coordinate) -> None:
        self._free_edges.remove(target)
        self.players[by].paths.add(target)

    def use_card(self, by: player.Nickname, card: WisdomCard) -> None:
        """
        Removes a card from the player's hand and adds it to the player's
        played cards.
        """
        self.players[by].cards[card] -= 1
        self.players[by].played_cards[card] += 1

    def take_resources(
        self,
        from_: player.Nickname,
        to: player.Nickname,
        amount: ResourceCount,
    ) -> None:
        """Exchanges resources between two players."""
        self.players[from_].resources.subtract(amount)
        self.players[to].resources.update(amount)

    def monopoly_of_resource(self, type: ResourceCard) -> None:
        """Takes all of a resource from a player and gives it the active player."""
        for nickname, player_ in self.players.items():
            if player_.resources[type] > 0:
                self.take_resources(
                    from_=nickname,
                    to=self.active_player,
                    amount=collections.Counter({type: player_.resources[type]}),
                )

    def take_from_supply(self, to: player.Nickname, amount: ResourceCount) -> None:
        """Takes resources from the supply and gives them to a specific player."""
        self.resource_supply.subtract(amount)
        self.players[to].resources.update(amount)

    def discard_resources(self, by: player.Nickname, amount: ResourceCount) -> None:
        """Discards resources from a player's hand."""
        self.players[by].resources.subtract(amount)
        self.resource_supply.update(amount)

    def take_wisdom_card(self, by: player.Nickname) -> WisdomCard:
        card = self.wisdom_deck.pop()
        self.players[by].cards_bought_this_turn[card] += 1
        return card

    def preserve_cards(self, by: player.Nickname) -> None:
        self.players[by].cards.update(self.players[by].cards_bought_this_turn)
        self.players[by].cards_bought_this_turn = collections.Counter()
