import collections
import dataclasses
import datetime
import itertools
import random
import uuid
from collections.abc import ItemsView, KeysView, Set, ValuesView
from types import MappingProxyType

import teyuna_shared


@dataclasses.dataclass
class SettlementsCollection:
    _locations: dict[teyuna_shared.Coordinate, teyuna_shared.SettlementType] = (
        dataclasses.field(
            default_factory=dict,
        )
    )
    _counts: collections.Counter[teyuna_shared.SettlementType] = dataclasses.field(
        default_factory=collections.Counter, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._counts = collections.Counter(self._locations.values())

    def __contains__(self, coord: teyuna_shared.Coordinate) -> bool:
        return coord in self._locations

    def __getitem__(
        self, coord: teyuna_shared.Coordinate
    ) -> teyuna_shared.SettlementType:
        return self._locations[coord]

    def __setitem__(
        self, coord: teyuna_shared.Coordinate, type: teyuna_shared.SettlementType
    ) -> None:
        if coord in self._locations:
            self._counts[self._locations[coord]] -= 1
        self._locations[coord] = type
        self._counts[type] += 1

    def locations(self) -> KeysView[teyuna_shared.Coordinate]:
        return self._locations.keys()

    def items(
        self,
    ) -> ItemsView[teyuna_shared.Coordinate, teyuna_shared.SettlementType]:
        return self._locations.items()

    def values(self) -> ValuesView[teyuna_shared.SettlementType]:
        return self._locations.values()

    def count(self, type: teyuna_shared.SettlementType) -> int:
        return self._counts[type]

    @property
    def counts(self) -> collections.Counter[teyuna_shared.SettlementType]:
        return collections.Counter(self._counts)


type CardCount = collections.Counter[teyuna_shared.WisdomCard]


def _default_resources() -> collections.Counter[teyuna_shared.ResourceCard]:
    return collections.Counter(
        {
            teyuna_shared.ResourceCard.GOLD: 0,
            teyuna_shared.ResourceCard.STONE: 0,
            teyuna_shared.ResourceCard.COTTON: 0,
            teyuna_shared.ResourceCard.MAIZE: 0,
            teyuna_shared.ResourceCard.WOOD: 0,
        }
    )


@dataclasses.dataclass(kw_only=True)
class Player:
    cards: CardCount = dataclasses.field(default_factory=collections.Counter)
    cards_bought_this_turn: CardCount = dataclasses.field(
        default_factory=collections.Counter
    )
    played_cards: CardCount = dataclasses.field(default_factory=collections.Counter)
    resources: collections.Counter[teyuna_shared.ResourceCard] = dataclasses.field(
        default_factory=_default_resources
    )
    settlements: SettlementsCollection = dataclasses.field(
        default_factory=SettlementsCollection
    )
    paths: set[teyuna_shared.Coordinate] = dataclasses.field(default_factory=set)


def _default_resource_supply() -> collections.Counter[teyuna_shared.ResourceCard]:
    return collections.Counter(
        {
            resource: teyuna_shared.RESOURCE_BANK_PER_TYPE
            for resource in teyuna_shared.ResourceCard
        }
    )


def _default_wisdom_deck() -> list[teyuna_shared.WisdomCard]:
    deck = [
        card
        for card, count in teyuna_shared.WISDOM_DECK_COUNTS.items()
        for _ in range(count)
    ]
    random.shuffle(deck)
    return deck


class GameAlreadyFullError(Exception):
    pass


class NicknameAlreadyTakenError(Exception):
    pass


@dataclasses.dataclass(kw_only=True)
class Game:
    map: tuple[teyuna_shared.MapHex, ...]
    players: dict[str, Player]
    conquistator_location: teyuna_shared.HexLocation
    harbours: tuple[teyuna_shared.HarbourPair, ...] = dataclasses.field(
        default_factory=teyuna_shared.default_harbour_pairs
    )
    available_slots: int = 4
    phase: teyuna_shared.GamePhaseName = teyuna_shared.GamePhaseName.LOBBY
    phase_deadline: datetime.datetime | None = None
    to_discard_resources: dict[str, int] = dataclasses.field(default_factory=dict)
    resource_supply: collections.Counter[teyuna_shared.ResourceCard] = (
        dataclasses.field(default_factory=_default_resource_supply)
    )
    wisdom_deck: list[teyuna_shared.WisdomCard] = dataclasses.field(
        default_factory=_default_wisdom_deck
    )
    trade_proposals: dict[uuid.UUID, teyuna_shared.TradeProposal] = dataclasses.field(
        default_factory=dict
    )
    longest_road: tuple[str | None, int] = dataclasses.field(
        default_factory=lambda: (None, 0)
    )
    biggest_army: tuple[str | None, int] = dataclasses.field(
        default_factory=lambda: (None, 0)
    )
    turns_played: int = 0
    player_idx: int = 0
    _turn_order: list[str] = dataclasses.field(
        default_factory=list, init=False, repr=False
    )
    _free_verticies: set[teyuna_shared.Coordinate] = dataclasses.field(init=False)
    _free_edges: set[teyuna_shared.Coordinate] = dataclasses.field(init=False)
    _restricted_verticies: set[teyuna_shared.Coordinate] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self._turn_order = []
        free_verticies: set[teyuna_shared.Coordinate] = set()
        free_edges: set[teyuna_shared.Coordinate] = set()
        for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
            if (q, r) not in teyuna_shared.INVALID_HEX_COORDINATES:
                free_verticies.add(teyuna_shared.canonical_vertex(q, r, d))
                free_edges.add(teyuna_shared.canonical_edge(q, r, d))
        self._free_verticies = free_verticies
        self._free_edges = free_edges
        self._restricted_verticies = set()

    @property
    def harbour_locations(
        self,
    ) -> MappingProxyType[teyuna_shared.Coordinate, teyuna_shared.ResourceCard | None]:
        return MappingProxyType(
            teyuna_shared.harbour_locations_from_pairs(self.harbours)
        )

    @property
    def turn_order(self) -> tuple[str, ...]:
        return tuple(self._turn_order)

    @property
    def active_player(self) -> str:
        return self._turn_order[self.player_idx]

    @property
    def victory_points(self) -> MappingProxyType[str, int]:
        return MappingProxyType(
            {
                nickname: victory_points(self, nickname)
                for nickname in self.players.keys()
            }
        )

    @property
    def free_verticies(self) -> Set[teyuna_shared.Coordinate]:
        """
        Returns all vertices that don't have a settlement on them,
        even if they are adjacent to a settlement and can't be used
        to place a settlement.
        """
        return frozenset(self._free_verticies)

    @property
    def free_edges(self) -> Set[teyuna_shared.Coordinate]:
        """Returns all edges that don't have a path on them"""
        return frozenset(self._free_edges)

    @property
    def restricted_verticies(self) -> Set[teyuna_shared.Coordinate]:
        """
        Returns all free vertices that can't be used to place a settlement,
        but are adjacent to a settlement and therore can't be used to place
        a settlement. Any path should be able to go through these verticies
        though.
        """
        return frozenset(self._restricted_verticies)

    def use_vertex(
        self,
        by: str,
        target: teyuna_shared.Coordinate,
        settlement: teyuna_shared.SettlementType,
    ) -> None:
        dq5, dr5 = teyuna_shared.delta_to_neighbor((target.d + 5) % 6)
        blocked_vertices: set[teyuna_shared.Coordinate] = set()
        for vq, vr, vd in (
            (target.q, target.r, (target.d + 1) % 6),
            (target.q, target.r, (target.d + 5) % 6),
            (target.q + dq5, target.r + dr5, (target.d + 1) % 6),
        ):
            try:
                blocked_vertices.add(teyuna_shared.canonical_vertex(vq, vr, vd))
            except ValueError:
                # Adjacent corner lies only on off-board / invalid hexes.
                continue
        self._free_verticies.remove(target)
        self._restricted_verticies.update(blocked_vertices)
        self.players[by].settlements[target] = settlement

    def use_edge(self, by: str, target: teyuna_shared.Coordinate) -> None:
        self._free_edges.remove(target)
        self.players[by].paths.add(target)

    def use_card(self, by: str, card: teyuna_shared.WisdomCard) -> None:
        """
        Removes a card from the player's hand and adds it to the player's
        played cards.
        """
        self.players[by].cards[card] -= 1
        self.players[by].played_cards[card] += 1

    def take_resources(
        self,
        from_: str,
        to: str,
        amount: teyuna_shared.ResourceCount,
    ) -> None:
        """Exchanges resources between two players."""
        self.players[from_].resources.subtract(amount)
        self.players[to].resources.update(amount)

    def monopoly_of_resource(self, type: teyuna_shared.ResourceCard) -> None:
        """Takes all of a resource from a player and gives it the active player."""
        for nickname, player_ in self.players.items():
            if player_.resources[type] > 0:
                self.take_resources(
                    from_=nickname,
                    to=self.active_player,
                    amount=collections.Counter({type: player_.resources[type]}),
                )

    def take_from_supply(self, to: str, amount: teyuna_shared.ResourceCount) -> None:
        """Takes resources from the supply and gives them to a specific player."""
        self.resource_supply.subtract(amount)
        self.players[to].resources.update(amount)

    def discard_resources(self, by: str, amount: teyuna_shared.ResourceCount) -> None:
        """Discards resources from a player's hand."""
        self.players[by].resources.subtract(amount)
        self.resource_supply.update(amount)

    def take_wisdom_card(self, by: str) -> teyuna_shared.WisdomCard:
        card = self.wisdom_deck.pop()
        self.players[by].cards_bought_this_turn[card] += 1
        return card

    def preserve_cards(self, by: str) -> None:
        self.players[by].cards.update(self.players[by].cards_bought_this_turn)
        self.players[by].cards_bought_this_turn = collections.Counter()

    def add_player(self, nickname: str) -> None:
        if self.available_slots <= 0:
            raise GameAlreadyFullError("game already full")
        if nickname in self.players:
            raise NicknameAlreadyTakenError("nickname already exists")
        self.players[nickname] = Player()
        self.available_slots -= 1

    def start(self, timeout_in: datetime.timedelta) -> None:
        self._turn_order = list(self.players.keys())
        random.shuffle(self._turn_order)
        self.player_idx = 0
        self.phase = teyuna_shared.GamePhaseName.FIRST_PLACEMENT
        self.phase_deadline = datetime.datetime.now(datetime.UTC) + timeout_in


def victory_points(game: Game, by: str, /) -> int:
    player_state = game.players[by]
    settlements = player_state.settlements
    points = settlements.count(
        teyuna_shared.SettlementType.TERRACE
    ) + 2 * settlements.count(teyuna_shared.SettlementType.GREAT_TERRACE)
    if game.longest_road[0] == by:
        points += 2
    if game.biggest_army[0] == by:
        points += 2
    points += player_state.played_cards[teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS]
    return points
