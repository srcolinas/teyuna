from __future__ import annotations

import abc
import dataclasses
import itertools
import threading
import random
import uuid


from ... import player
from .. import entities, ports
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class AddInitialBuildingsAction:
    terrace: entities.Coordinate
    path: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildTerraceAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildGreatTerraceAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildPathAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class ProposeTradeToPlayerInTurnAction:
    offer: entities.ResourceCount
    request: entities.ResourceCount


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptTradeProposalAction:
    id: uuid.UUID


@dataclasses.dataclass(frozen=True, slots=True)
class TradeWithSupplyAction:
    offers: entities.ResourceCard
    requests: entities.ResourceCard


PlayerAction = (
    BuildTerraceAction
    | BuildGreatTerraceAction
    | BuildPathAction
    | ProposeTradeToPlayerInTurnAction
    | AcceptTradeProposalAction
    | TradeWithSupplyAction
    | AddInitialBuildingsAction
)


@dataclasses.dataclass
class PlayerRequest:
    by: player.Nickname
    action: PlayerAction


class GamePhaseNode(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> entities.GamePhaseName: ...

    @abc.abstractmethod
    def process_player_request(
        self, game: entities.ActiveGame, request: PlayerRequest
    ) -> entities.GamePhaseName | None:
        """Handle a player request.

        Returns the next phase when the phase is finished and the manager should advance
        to ``next``; None when the game remains in this phase.
        """

    def on_enter(self, game: entities.ActiveGame) -> None:
        return

    def on_exit(self, game: entities.ActiveGame) -> None:
        return


class ActiveGameDoesNotExistError(Exception): ...


class GameManager:
    def __init__(
        self,
        initial_phase: GamePhaseNode,
        graph: dict[uuid.UUID, tuple[uuid.UUID, ...]],
    ):
        self._repository: dict[
            uuid.UUID, tuple[entities.ActiveGame, GamePhaseNode]
        ] = {}
        self._phase = initial_phase
        self._phase_change_lock = threading.Lock()

    def advance_phase(
        self,
        game_id: uuid.UUID,
        *,
        by: player.Nickname | None = None,
    ) -> None:
        game, phase = self._repository[game_id]
        if by is not None and by != game.active_player:
            raise _errors.PlayerNotInTurn(f"Player {by} is not in turn")
        with self._phase_change_lock:
            if game.phase != phase.valid_phase:
                raise _errors.InvalidGamePhase(
                    f"Game is in {game.phase}, but manager is in {phase.valid_phase}"
                )
            self._transition(game)
        self._repository.update(game_id, game)

    def process_player_request(
        self, game_id: uuid.UUID, request: PlayerRequest
    ) -> None:
        game = self._repository.retrieve(game_id)
        if game.phase != self._phase.valid_phase:
            raise _errors.InvalidGamePhase(
                f"Player {request.by} can only make requests in the"
                f" {self._phase.valid_phase} phase"
            )
        next = self._phase.process_player_request(game, request)
        if next:
            with self._phase_change_lock:
                self._transition(game_id, next)
                self._repository.update(game_id, game)

    def _transition(self, game: entities.ActiveGame) -> None:
        ...
        


    def create(self, players: list[player.Nickname]) -> uuid.UUID:
        map = _generate_map()
        deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
        players = list(players)
        random.shuffle(players)
        free_verticies, free_edges = _initial_buildable_locations()
        game = entities.ActiveGame(
            map=map,
            conquistator_location=random.choice(deserts),
            turn_order=tuple(players),
            players={nickname: entities.Player() for nickname in players},
            free_verticies=free_verticies,
            free_edges=free_edges,
        )
        return game

    def retrieve(self, id: uuid.UUID) -> ports.ActiveGame:
        game, phase = self._repository[id]

        players, settlements, paths = [], [], []
        for nickname, entity_player in game.players.items():
            players.append(_to_port_player(nickname, entity_player))
            for location, type in player.settlements.items():
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
            id=id,
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
            turn_order=list(game.turn_order[game.player_idx :])
            + list(game.turn_order[: game.player_idx]),
            phase=phase.name,
        )

    def _validate_game_exists(self, id: uuid.UUID) -> None:
        if id not in self._repository:
            raise ActiveGameDoesNotExistError(f"Game {id} does not exist")


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


def _initial_buildable_locations() -> tuple[
    set[entities.Coordinate], set[entities.Coordinate]
]:
    free_verticies: set[entities.Coordinate] = set()
    free_edges: set[entities.Coordinate] = set()
    for item in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if item not in entities.INVALID_HEX_COORDINATES:
            free_verticies.add(_map.canonical_vertex(*item))
            free_edges.add(_map.canonical_edge(*item))
    return free_verticies, free_edges


def _generate_map() -> tuple[entities.Hex, ...]:
    random.shuffle(_TYPES)
    random.shuffle(_NUMBERS)

    map = []
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
            map.append(
                entities.Hex(
                    q=q,
                    r=r,
                    type=type,
                    number=number,
                )
            )

    return tuple(map)


_TYPES = (
    [entities.HexType.MOUNTAINS] * 3
    + [entities.HexType.QUARRIES] * 3
    + [entities.HexType.HIGHLANDS] * 4
    + [entities.HexType.VALLEYS] * 4
    + [entities.HexType.JUNGLE] * 4
    + [entities.HexType.DESERT]
)
_NUMBERS = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
