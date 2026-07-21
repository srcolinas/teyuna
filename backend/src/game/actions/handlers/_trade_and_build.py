import collections
from typing import Final

import pydantic

from ... import player
from ... import entities
from .. import _registry
from . import _placement
from ._longest_road import recompute_longest_road, update_longest_road
from ._play_card import PlayWisdomCardAction, PlayedWisdomCardResult, play_wisdom_card
from ._victory import phase_after_victory_check


class BuildSettlementAction(_registry.PlayerAction):
    item: entities.SettlementType
    coordinate: entities.Coordinate

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "BuildSettlementAction":
        object.__setattr__(
            self,
            "coordinate",
            entities.canonical_vertex(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )
        return self


class BuiltSettlementResult(_registry.ActionExecutionResult):
    item: entities.SettlementType | None = None
    coordinate: entities.Coordinate | None = None


class BuildPathAction(_registry.PlayerAction):
    coordinate: entities.Coordinate

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "BuildPathAction":
        object.__setattr__(
            self,
            "coordinate",
            entities.canonical_edge(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )
        return self


class BuiltPathResult(_registry.ActionExecutionResult):
    coordinate: entities.Coordinate | None = None


class EndedTradeAndBuildResult(_registry.ActionExecutionResult):
    next_player: player.Nickname = ""


class BuyWisdomCardAction(_registry.PlayerAction):
    pass


class BoughtWisdomCardResult(_registry.ActionExecutionResult):
    card: entities.WisdomCard | None = None


def handle_build_terrace(
    game: entities.Game, action: BuildSettlementAction
) -> BuiltSettlementResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if action.item is entities.SettlementType.TERRACE:
        error = _build_terrace(game, action.by, action.coordinate)
    else:
        error = _build_great_terrace(game, action.by, action.coordinate)
    if error is not None:
        return BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    game.phase = phase_after_victory_check(
        game, action.by, entities.GamePhaseName.TRADE_AND_BUILD
    )
    return BuiltSettlementResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        item=action.item,
        coordinate=action.coordinate,
    )


def handle_build_path(game: entities.Game, action: BuildPathAction) -> BuiltPathResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    error = _build_path(game, action.by, action.coordinate)
    if error is not None:
        return BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = phase_after_victory_check(
        game, action.by, entities.GamePhaseName.TRADE_AND_BUILD
    )
    return BuiltPathResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        coordinate=action.coordinate,
    )


def handle_end_trade_and_build(
    game: entities.Game, action: _registry.PlayerAction
) -> EndedTradeAndBuildResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return EndedTradeAndBuildResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    game.preserve_cards(action.by)
    game.trade_proposals.clear()

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
    else:
        game.player_idx = 0
    game.phase = entities.GamePhaseName.DICE_ROLL

    return EndedTradeAndBuildResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        next_player=game.active_player,
    )


def handle_buy_wisdom_card(
    game: entities.Game, action: BuyWisdomCardAction
) -> BoughtWisdomCardResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if not game.wisdom_deck:
        return BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="Cannot buy more wisdom cards",
        )

    error = _ensure_resources(game.players[action.by].resources, _WISDOM_CARD_COST)
    if error is not None:
        return BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.discard_resources(action.by, _WISDOM_CARD_COST)
    card = game.take_wisdom_card(action.by)
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return BoughtWisdomCardResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        card=card,
    )


def handle_trade_and_build_play_wisdom_card(
    game: entities.Game, action: PlayWisdomCardAction
) -> PlayedWisdomCardResult:
    return play_wisdom_card(
        game,
        action,
        card_phases=_TRADE_AND_BUILD_CARD_PHASES,
        phase_label="trade and build",
    )


def _build_terrace(
    game: entities.Game, by: player.Nickname, coordinate: entities.Coordinate
) -> str | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, _TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(entities.SettlementType.TERRACE)
        >= entities.MAX_TERRACES
    ):
        return "No terraces remaining"

    can = _placement.can_build_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        existing_paths=player_state.paths,
        target=coordinate,
    )
    if not can:
        return _placement.format_invalid_settlement_location(
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
    game: entities.Game, by: player.Nickname, coordinate: entities.Coordinate
) -> str | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, _GREAT_TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(entities.SettlementType.GREAT_TERRACE)
        >= entities.MAX_GREAT_TERRACES
    ):
        return "No great terraces remaining"

    settlements = player_state.settlements
    if coordinate not in settlements:
        return _placement.format_invalid_settlement_location(
            target=coordinate,
            player=by,
            free_vertices=game.free_verticies,
            restricted_vertices=game.restricted_verticies,
            existing_paths=player_state.paths,
            existing_settlements=dict(settlements.items()),
            reason="You must first build a terrace at specified location.",
        )
    if settlements[coordinate] is entities.SettlementType.GREAT_TERRACE:
        return _placement.format_invalid_settlement_location(
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
    game: entities.Game, by: player.Nickname, coordinate: entities.Coordinate
) -> str | None:
    player_state = game.players[by]
    if len(player_state.paths) >= entities.MAX_PATHS:
        return "No paths remaining"
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
        return _placement.format_invalid_path_location(
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
) -> str | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return f"Insufficient {resource.value} to build"
    return None


_TRADE_AND_BUILD_CARD_PHASES: Final[
    dict[entities.WisdomCard, entities.GamePhaseName]
] = {
    entities.WisdomCard.WARRIOR: entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
    entities.WisdomCard.WINDOM_OF_MAMO: entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
    entities.WisdomCard.BLESSING_OF_ALUNA: (
        entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED
    ),
    entities.WisdomCard.PATHFINDER: (
        entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER
    ),
    entities.WisdomCard.LEGACY_OF_THE_ELDERS: entities.GamePhaseName.TRADE_AND_BUILD,
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
