import itertools
import random
import uuid
import collections
from collections.abc import Sequence
from typing import Any


from ... import player
from .. import entities, ports
from . import phases

PhaseNode = phases.GamePhaseNode[Any, Any, Any]


class ActiveGameDoesNotExistError(Exception): ...


class GamePhaseNodeNotConfiguredError(Exception):
    """Raised when a required phase node was not provided to the manager."""


class GameManager:
    def __init__(
        self,
        nodes: dict[phases.GamePhaseName, PhaseNode],
        start: phases.GamePhaseName = phases.GamePhaseName.FIRST_PLACEMENT,
    ):
        self._memory: dict[uuid.UUID, tuple[entities.ActiveGame, PhaseNode]] = {}
        self._nodes = nodes
        self._start = start

    def create_game(self, players: Sequence[player.Nickname]) -> uuid.UUID:
        game = _create_new(players)
        game_id = uuid.uuid4()
        self._memory[game_id] = (game, self._require_node(self._start))
        return game_id

    def run(self, game_id: uuid.UUID, request: phases.PlayerRequest) -> list[Any]:
        game, phase = self._validate_game_exists(game_id)
        reports: list[Any] = []
        step = phase.run(game, request)
        if step.value is not None:
            reports.append(step.value)
        if step.finished:
            leaving = phase.on_exit(game)
            if leaving.value is not None:
                reports.append(leaving.value)
            phase = self._require_node(leaving.next)
            entering = phase.on_enter(game)
            if entering.value is not None:
                reports.append(entering.value)
            self._memory[game_id] = (game, phase)
        return reports

    def retrieve(self, game_id: uuid.UUID) -> ports.ActiveGame:
        game, _ = self._validate_game_exists(game_id)
        players, settlements, paths = [], [], []
        for nickname, entity_player in game.players.items():
            players.append(_to_port_player(nickname, entity_player))
            for location, type in entity_player.settlements.items():
                settlements.append(
                    ports.PlayedSettlement(
                        location=ports.VertexCoordinate(
                            hex_coord=ports.HexCoordinate(q=location.q, r=location.r),
                            direction=location.d,
                        ),
                        type=type,
                        owner=nickname,
                    )
                )
            for path in entity_player.paths:
                paths.append(
                    ports.PlayedStonePath(
                        owner=nickname,
                        location=ports.EdgeCoordinate(
                            hex_coord=ports.HexCoordinate(q=path.q, r=path.r),
                            direction=path.d,
                        ),
                    )
                )

        return ports.ActiveGame(
            id=game_id,
            map=tuple(
                ports.Hex(
                    coordinate=ports.HexCoordinate(q=hex.q, r=hex.r),
                    type=hex.type,
                    number=hex.number,
                )
                for hex in game.map
            ),
            conquistator_location=ports.HexCoordinate(
                q=game.conquistator_location.q, r=game.conquistator_location.r
            ),
            players=players,
            settlements=settlements,
            paths=paths,
            turn_order=game.turn_order[game.player_idx :]
            + game.turn_order[: game.player_idx],
        )

    def _require_node(self, phase: phases.GamePhaseName) -> PhaseNode:
        try:
            return self._nodes[phase]
        except KeyError:
            raise GamePhaseNodeNotConfiguredError(
                f"No GamePhaseNode configured for phase {phase.value!r}."
            ) from None

    def _validate_game_exists(
        self, id: uuid.UUID
    ) -> tuple[entities.ActiveGame, PhaseNode]:
        if id not in self._memory:
            raise ActiveGameDoesNotExistError(f"Game {id} does not exist")
        return self._memory[id]


def _create_new(players: Sequence[player.Nickname]) -> entities.ActiveGame:
    map = _generate_map()
    deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
    players = list(players)
    random.shuffle(players)
    free_verticies, free_edges = _initial_buildable_locations()
    desert = random.choice(deserts)
    return entities.ActiveGame(
        map=map,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        turn_order=tuple(players),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in players
        },
        free_verticies=free_verticies,
        free_edges=free_edges,
        wisdom_deck=_create_wisdom_deck(),
    )


def _create_wisdom_deck() -> list[entities.WisdomCard]:
    deck = (
        [entities.WisdomCard.WARRIOR] * 14
        + [entities.WisdomCard.LEGACY_OF_THE_ELDERS] * 5
        + [entities.WisdomCard.PATHFINDER] * 2
        + [entities.WisdomCard.BLESSING_OF_ALUNA] * 2
        + [entities.WisdomCard.WINDOM_OF_MAMO] * 2
    )
    random.shuffle(deck)
    return deck


def _initial_buildable_locations() -> tuple[
    set[entities.Coordinate], set[entities.Coordinate]
]:
    free_verticies: set[entities.Coordinate] = set()
    free_edges: set[entities.Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in entities.INVALID_HEX_COORDINATES:
            free_verticies.add(entities.canonical_vertex(q, r, d))
            free_edges.add(entities.canonical_edge(q, r, d))
    return free_verticies, free_edges


def _generate_map() -> tuple[entities.Hex, ...]:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    tiles = []
    type_idx = -1
    number_idx = -1
    for q in range(-2, 3):
        for r in range(-2, 3):
            if (q, r) in entities.INVALID_HEX_COORDINATES:
                continue
            type_idx += 1
            type = _TYPES[type_idx]
            if type is entities.HexType.DESERT:
                number = 7
            else:
                number_idx += 1
                number = _NUMBERS[number_idx]
            tiles.append(
                entities.Hex(
                    q=q,
                    r=r,
                    type=type,
                    number=number,
                )
            )

    return tuple(tiles)


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2


def _to_port_player(
    nickname: player.Nickname, entity_player: entities.Player
) -> ports.Player:
    counts = entity_player.settlements.counts
    return ports.Player(
        nickname=nickname,
        played_wisdom_cards=[
            card
            for card, count in entity_player.played_cards.items()
            for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(entity_player.cards.values()),
        num_resources=sum(entity_player.resources.values()),
        available_terraces=entities.MAX_TERRACES
        - counts[entities.SettlementType.TERRACE],
        available_great_terraces=entities.MAX_GREAT_TERRACES
        - counts[entities.SettlementType.GREAT_TERRACE],
        available_paths=entities.MAX_PATHS - len(entity_player.paths),
    )
