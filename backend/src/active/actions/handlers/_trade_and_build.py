import collections
import dataclasses
from typing import Final

from .... import player
from ... import entities
from .. import _registry, _results
from . import _errors, _placement
from ._longest_road import recompute_longest_road, update_longest_road
from ._play_card import PlayWisdomCardAction, play_wisdom_card
from ._victory import phase_after_victory_check


@dataclasses.dataclass(frozen=True, slots=True)
class BuildSettlementAction(_registry.PlayerAction):
    item: entities.SettlementType
    coordinate: entities.Coordinate

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "coordinate",
            entities.canonical_vertex(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class BuildPathAction(_registry.PlayerAction):
    coordinate: entities.Coordinate

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "coordinate",
            entities.canonical_edge(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class BuyWisdomCardAction(_registry.PlayerAction):
    pass


def handle_build_terrace(
    game: entities.ActiveGame, action: BuildSettlementAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
        )

    if action.item is entities.SettlementType.TERRACE:
        error = _build_terrace(game, action.by, action.coordinate)
    else:
        error = _build_great_terrace(game, action.by, action.coordinate)
    if error is not None:
        return _results.fail(error)

    return _results.ok(
        phase_after_victory_check(
            game, action.by, _registry.GamePhaseName.TRADE_AND_BUILD
        )
    )


def handle_build_path(
    game: entities.ActiveGame, action: BuildPathAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
        )

    error = _build_path(game, action.by, action.coordinate)
    if error is not None:
        return _results.fail(error)
    return _results.ok(
        phase_after_victory_check(
            game, action.by, _registry.GamePhaseName.TRADE_AND_BUILD
        )
    )


def handle_end_trade_and_build(
    game: entities.ActiveGame, action: _registry.PlayerAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
        )

    game.preserve_cards(action.by)
    game.trade_proposals.clear()

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
    else:
        game.player_idx = 0

    return _results.ok(_registry.GamePhaseName.DICE_ROLL)


def handle_buy_wisdom_card(
    game: entities.ActiveGame, action: BuyWisdomCardAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
        )

    if not game.wisdom_deck:
        return _results.fail(
            _errors.EmptyWisdomDeckError("Cannot buy more wisdom cards")
        )

    error = _ensure_resources(game.players[action.by].resources, _WISDOM_CARD_COST)
    if error is not None:
        return _results.fail(error)
    game.discard_resources(action.by, _WISDOM_CARD_COST)
    game.take_wisdom_card(action.by)
    return _results.ok(_registry.GamePhaseName.TRADE_AND_BUILD)


def handle_trade_and_build_play_wisdom_card(
    game: entities.ActiveGame, action: PlayWisdomCardAction
) -> _registry.ActionExecutionResult:
    return play_wisdom_card(
        game,
        action,
        card_phases=_TRADE_AND_BUILD_CARD_PHASES,
        phase_label="trade and build",
    )


def _build_terrace(
    game: entities.ActiveGame, by: player.Nickname, coordinate: entities.Coordinate
) -> Exception | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, _TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(entities.SettlementType.TERRACE)
        >= entities.MAX_TERRACES
    ):
        return _errors.InsufficientResourcesError("No terraces remaining")

    can = _placement.can_build_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        existing_paths=player_state.paths,
        target=coordinate,
    )
    if not can:
        return _errors.InvalidSettlementLocation(
            target=coordinate,
            player=by,
            free_vertices=game.free_verticies,
            restricted_vertices=game.restricted_verticies,
            existing_paths=player_state.paths,
        )

    game.use_vertex(by, coordinate, entities.SettlementType.TERRACE)
    game.discard_resources(by, _TERRACE_COST)
    recompute_longest_road(game, by, vertex=coordinate)
    return None


def _build_great_terrace(
    game: entities.ActiveGame, by: player.Nickname, coordinate: entities.Coordinate
) -> Exception | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, _GREAT_TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(entities.SettlementType.GREAT_TERRACE)
        >= entities.MAX_GREAT_TERRACES
    ):
        return _errors.InsufficientResourcesError("No great terraces remaining")

    settlements = player_state.settlements
    if coordinate not in settlements:
        return _errors.InvalidSettlementLocation(
            target=coordinate,
            player=by,
            free_vertices=game.free_verticies,
            restricted_vertices=game.restricted_verticies,
            existing_paths=player_state.paths,
            existing_settlements=dict(settlements.items()),
            reason="You must first build a terrace at specified location.",
        )
    if settlements[coordinate] is entities.SettlementType.GREAT_TERRACE:
        return _errors.InvalidSettlementLocation(
            target=coordinate,
            player=by,
            free_vertices=game.free_verticies,
            restricted_vertices=game.restricted_verticies,
            existing_paths=player_state.paths,
            existing_settlements=dict(settlements.items()),
            reason="You have already built a great terrace at specified location.",
        )

    settlements[coordinate] = entities.SettlementType.GREAT_TERRACE
    game.discard_resources(by, _GREAT_TERRACE_COST)
    return None


def _build_path(
    game: entities.ActiveGame, by: player.Nickname, coordinate: entities.Coordinate
) -> Exception | None:
    player_state = game.players[by]
    if len(player_state.paths) >= entities.MAX_PATHS:
        return _errors.InsufficientResourcesError("No paths remaining")
    error = _ensure_resources(player_state.resources, _PATH_COST)
    if error is not None:
        return error

    can = _placement.can_add_free_path_at(
        target=coordinate,
        free_edges=game.free_edges,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_vertices=game.free_verticies,
    )
    if not can:
        return _errors.InvalidPathLocation(
            target=coordinate,
            player=by,
            existing_settlements=player_state.settlements.locations(),
            existing_paths=player_state.paths,
            free_edges=game.free_edges,
        )

    game.use_edge(by, coordinate)
    game.discard_resources(by, _PATH_COST)
    update_longest_road(game, by, edge=coordinate)
    return None


def _ensure_resources(
    resources: entities.ResourceCount, cost: entities.ResourceCount
) -> Exception | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return _errors.InsufficientResourcesError(
                f"Insufficient {resource.value} to build"
            )
    return None


_TRADE_AND_BUILD_CARD_PHASES: Final[
    dict[entities.WisdomCard, _registry.GamePhaseName]
] = {
    entities.WisdomCard.WARRIOR: _registry.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
    entities.WisdomCard.WINDOM_OF_MAMO: _registry.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
    entities.WisdomCard.BLESSING_OF_ALUNA: (
        _registry.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED
    ),
    entities.WisdomCard.PATHFINDER: (
        _registry.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER
    ),
    entities.WisdomCard.LEGACY_OF_THE_ELDERS: _registry.GamePhaseName.TRADE_AND_BUILD,
}


_TERRACE_COST: Final[entities.ResourceCount] = collections.Counter(
    {
        entities.ResourceCard.STONE: 1,
        entities.ResourceCard.WOOD: 1,
        entities.ResourceCard.COTTON: 1,
        entities.ResourceCard.MAIZE: 1,
    }
)
_GREAT_TERRACE_COST: Final[entities.ResourceCount] = collections.Counter(
    {
        entities.ResourceCard.GOLD: 3,
        entities.ResourceCard.MAIZE: 2,
    }
)
_PATH_COST: Final[entities.ResourceCount] = collections.Counter(
    {
        entities.ResourceCard.STONE: 1,
        entities.ResourceCard.WOOD: 1,
    }
)
_WISDOM_CARD_COST: Final[entities.ResourceCount] = collections.Counter(
    {
        entities.ResourceCard.GOLD: 1,
        entities.ResourceCard.COTTON: 1,
        entities.ResourceCard.MAIZE: 1,
    }
)
