from typing import Final

import teyuna_shared

from ... import entities
from . import _placement, _longest_road, _victory, _play_card


def handle_build_terrace(
    game: entities.Game, action: teyuna_shared.BuildSettlementAction
) -> teyuna_shared.BuiltSettlementResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if action.item is teyuna_shared.SettlementType.TERRACE:
        error = _build_terrace(game, action.by, action.coordinate)
    else:
        error = _build_great_terrace(game, action.by, action.coordinate)
    if error is not None:
        return teyuna_shared.BuiltSettlementResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    game.phase = _victory.phase_after_victory_check(
        game, action.by, teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_shared.BuiltSettlementResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        item=action.item,
        coordinate=action.coordinate,
    )


def handle_build_path(
    game: entities.Game, action: teyuna_shared.BuildPathAction
) -> teyuna_shared.BuiltPathResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    error = _build_path(game, action.by, action.coordinate)
    if error is not None:
        return teyuna_shared.BuiltPathResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, action.by, teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_shared.BuiltPathResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        coordinate=action.coordinate,
    )


def handle_end_trade_and_build(
    game: entities.Game, action: teyuna_shared.PlayerAction
) -> teyuna_shared.EndedTradeAndBuildResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.EndedTradeAndBuildResult(
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
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL

    return teyuna_shared.EndedTradeAndBuildResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        next_player=game.active_player,
    )


def handle_buy_wisdom_card(
    game: entities.Game, action: teyuna_shared.BuyWisdomCardAction
) -> teyuna_shared.BoughtWisdomCardResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if not game.wisdom_deck:
        return teyuna_shared.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="Cannot buy more wisdom cards",
        )

    error = _ensure_resources(
        game.players[action.by].resources, teyuna_shared.WISDOM_CARD_COST
    )
    if error is not None:
        return teyuna_shared.BoughtWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.discard_resources(action.by, teyuna_shared.WISDOM_CARD_COST)
    card = game.take_wisdom_card(action.by)
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    return teyuna_shared.BoughtWisdomCardResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        card=card,
    )


def handle_trade_and_build_play_wisdom_card(
    game: entities.Game, action: teyuna_shared.PlayWisdomCardAction
) -> teyuna_shared.PlayedWisdomCardResult:
    return _play_card.play_wisdom_card(
        game,
        action,
        card_phases=_TRADE_AND_BUILD_CARD_PHASES,
        phase_label="trade and build",
    )


def _build_terrace(
    game: entities.Game, by: str, coordinate: teyuna_shared.Coordinate
) -> str | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, teyuna_shared.TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(teyuna_shared.SettlementType.TERRACE)
        >= teyuna_shared.MAX_TERRACES
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

    game.use_vertex(by, coordinate, teyuna_shared.SettlementType.TERRACE)
    game.discard_resources(by, teyuna_shared.TERRACE_COST)
    _longest_road.recompute_longest_road(game, by, vertex=coordinate)
    return None


def _build_great_terrace(
    game: entities.Game, by: str, coordinate: teyuna_shared.Coordinate
) -> str | None:
    player_state = game.players[by]
    error = _ensure_resources(player_state.resources, teyuna_shared.GREAT_TERRACE_COST)
    if error is not None:
        return error
    if (
        player_state.settlements.count(teyuna_shared.SettlementType.GREAT_TERRACE)
        >= teyuna_shared.MAX_GREAT_TERRACES
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
    if settlements[coordinate] is teyuna_shared.SettlementType.GREAT_TERRACE:
        return _placement.format_invalid_settlement_location(
            target=coordinate,
            player=by,
            free_vertices=game.free_verticies,
            restricted_vertices=game.restricted_verticies,
            existing_paths=player_state.paths,
            existing_settlements=dict(settlements.items()),
            reason="You have already built a great terrace at specified location.",
        )

    settlements[coordinate] = teyuna_shared.SettlementType.GREAT_TERRACE
    game.discard_resources(by, teyuna_shared.GREAT_TERRACE_COST)
    return None


def _build_path(
    game: entities.Game, by: str, coordinate: teyuna_shared.Coordinate
) -> str | None:
    player_state = game.players[by]
    if len(player_state.paths) >= teyuna_shared.MAX_PATHS:
        return "No paths remaining"
    error = _ensure_resources(player_state.resources, teyuna_shared.PATH_COST)
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
    game.discard_resources(by, teyuna_shared.PATH_COST)
    _longest_road.update_longest_road(game, by, edge=coordinate)
    return None


def _ensure_resources(
    resources: teyuna_shared.ResourceCount, cost: teyuna_shared.ResourceCount
) -> str | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return f"Insufficient {resource.value} to build"
    return None


_TRADE_AND_BUILD_CARD_PHASES: Final[
    dict[teyuna_shared.WisdomCard, teyuna_shared.GamePhaseName]
] = {
    teyuna_shared.WisdomCard.WARRIOR: teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
    teyuna_shared.WisdomCard.WINDOM_OF_MAMO: teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
    teyuna_shared.WisdomCard.BLESSING_OF_ALUNA: (
        teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED
    ),
    teyuna_shared.WisdomCard.PATHFINDER: (
        teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER
    ),
    teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS: teyuna_shared.GamePhaseName.TRADE_AND_BUILD,
}
