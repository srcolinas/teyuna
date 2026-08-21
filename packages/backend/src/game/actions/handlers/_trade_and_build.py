from typing import Final

import teyuna_core

from ... import entities
from .. import _execution
from . import _placement, _longest_road, _victory, _play_card


def handle_build_terrace(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuildSettlementAction,
) -> teyuna_core.BuiltSettlementResult:
    previous_phase = game.phase
    if game.active_player != context.by:
        return teyuna_core.BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} is not in turn",
        )

    if action.item is teyuna_core.SettlementType.TERRACE:
        error = _build_terrace(game, context, action)
    else:
        error = _build_great_terrace(game, context, action)
    if error is not None:
        return teyuna_core.BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    game.phase = _victory.phase_after_victory_check(
        game, context.by, teyuna_core.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_core.BuiltSettlementResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        item=action.item,
        coordinate=action.coordinate,
    )


def handle_build_path(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuildPathAction,
) -> teyuna_core.BuiltPathResult:
    previous_phase = game.phase
    if game.active_player != context.by:
        return teyuna_core.BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} is not in turn",
        )

    error = _build_path(game, context, action)
    if error is not None:
        return teyuna_core.BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, context.by, teyuna_core.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_core.BuiltPathResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        coordinate=action.coordinate,
    )


def handle_end_trade_and_build(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayerAction,
) -> teyuna_core.EndedTradeAndBuildResult:
    previous_phase = game.phase
    if game.active_player != context.by:
        return teyuna_core.EndedTradeAndBuildResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} is not in turn",
        )

    game.preserve_cards(context.by)
    game.trade_proposals.clear()

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
    else:
        game.player_idx = 0
    game.turns_played += 1
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL

    return teyuna_core.EndedTradeAndBuildResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        next_player=game.active_player,
    )


def handle_buy_wisdom_card(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuyWisdomCardAction,
) -> teyuna_core.BoughtWisdomCardResult:
    previous_phase = game.phase
    if game.active_player != context.by:
        return teyuna_core.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} is not in turn",
        )

    if not game.wisdom_deck:
        return teyuna_core.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="Cannot buy more wisdom cards",
        )

    error = _ensure_resources(
        game.players[context.by].resources, teyuna_core.WISDOM_CARD_COST
    )
    if error is not None:
        return teyuna_core.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.discard_resources(context.by, teyuna_core.WISDOM_CARD_COST)
    card = game.take_wisdom_card(context.by)
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    return teyuna_core.BoughtWisdomCardResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        card=card,
    )


def handle_trade_and_build_play_wisdom_card(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayWisdomCardAction,
) -> teyuna_core.PlayedWisdomCardResult:
    return _play_card.play_wisdom_card(
        game,
        context,
        action,
        card_phases=_TRADE_AND_BUILD_CARD_PHASES,
        phase_label="trade and build",
    )


def _build_terrace(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuildSettlementAction,
) -> str | None:
    player_state = game.players[context.by]
    error = _ensure_resources(player_state.resources, teyuna_core.TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(teyuna_core.SettlementType.TERRACE)
        >= teyuna_core.MAX_TERRACES
    ):
        return "No terraces remaining"

    can = _placement.can_build_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        existing_paths=player_state.paths,
        target=action.coordinate,
    )
    if not can:
        return _placement.format_invalid_settlement_location(
            target=action.coordinate,
            player=context.by,
        )

    game.use_vertex(
        context.by,
        action.coordinate,
        teyuna_core.SettlementType.TERRACE,
    )
    game.discard_resources(context.by, teyuna_core.TERRACE_COST)
    _longest_road.recompute_longest_road(game, vertex=action.coordinate)
    return None


def _build_great_terrace(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuildSettlementAction,
) -> str | None:
    player_state = game.players[context.by]
    error = _ensure_resources(player_state.resources, teyuna_core.GREAT_TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(teyuna_core.SettlementType.GREAT_TERRACE)
        >= teyuna_core.MAX_GREAT_TERRACES
    ):
        return "No great terraces remaining"

    settlements = player_state.settlements
    if action.coordinate not in settlements:
        return _placement.format_invalid_settlement_location(
            target=action.coordinate,
            player=context.by,
            reason="You must first build a terrace at specified location.",
        )
    if settlements[action.coordinate] is teyuna_core.SettlementType.GREAT_TERRACE:
        return _placement.format_invalid_settlement_location(
            target=action.coordinate,
            player=context.by,
            reason="You have already built a great terrace at specified location.",
        )

    settlements[action.coordinate] = teyuna_core.SettlementType.GREAT_TERRACE
    game.discard_resources(context.by, teyuna_core.GREAT_TERRACE_COST)
    return None


def _build_path(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.BuildPathAction,
) -> str | None:
    player_state = game.players[context.by]
    if len(player_state.paths) >= teyuna_core.MAX_PATHS:
        return "No paths remaining"
    error = _ensure_resources(player_state.resources, teyuna_core.PATH_COST)
    if error is not None:
        return error

    can = _placement.can_add_free_path_at(
        target=action.coordinate,
        free_edges=game.free_edges,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_vertices=game.free_verticies,
    )
    if not can:
        return _placement.format_invalid_path_location(
            target=action.coordinate,
            player=context.by,
        )

    game.use_edge(context.by, action.coordinate)
    game.discard_resources(context.by, teyuna_core.PATH_COST)
    _longest_road.maybe_add_to_longest_road(game, context.by, edge=action.coordinate)
    return None


def _ensure_resources(
    resources: teyuna_core.ResourceCount, cost: teyuna_core.ResourceCount
) -> str | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return f"Insufficient {resource.value} to build"
    return None


_TRADE_AND_BUILD_CARD_PHASES: Final[
    dict[teyuna_core.WisdomCard, teyuna_core.GamePhaseName]
] = {
    teyuna_core.WisdomCard.WARRIOR: teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
    teyuna_core.WisdomCard.WISDOM_OF_MAMO: teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
    teyuna_core.WisdomCard.BLESSING_OF_ALUNA: (
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED
    ),
    teyuna_core.WisdomCard.PATHFINDER: (
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER
    ),
    teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS: teyuna_core.GamePhaseName.TRADE_AND_BUILD,
}
