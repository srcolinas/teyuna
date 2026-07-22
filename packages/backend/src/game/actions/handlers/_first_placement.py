import teyuna_shared

from ... import entities
from .. import timeouts
from . import _placement


def handle_first_placement(
    game: entities.Game, action: teyuna_shared.FreePlacementAction
) -> teyuna_shared.PlacedBuildingsResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    action = timeouts.resolve_free_placement(
        game,
        action.rng_,
        by=action.by,
        terrace=action.terrace,
        path=action.path,
        due_to_timeout=action.due_to_timeout,
    )
    if action.terrace is None or action.path is None:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="Could not resolve a legal free placement",
        )

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=_placement.format_invalid_settlement_location(
                target=action.terrace,
                player=action.by,
                free_vertices=game.free_verticies,
                restricted_vertices=game.restricted_verticies,
            ),
        )

    player_state = game.players[action.by]
    can = _placement.can_add_free_path_at(
        target=action.path,
        free_edges=game.free_edges,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_vertices=game.free_verticies,
        new_settlement=action.terrace,
    )
    if not can:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=_placement.format_invalid_path_location(
                target=action.path,
                player=action.by,
                existing_settlements=player_state.settlements.locations(),
                existing_paths=player_state.paths,
                free_edges=game.free_edges,
            ),
        )

    game.use_vertex(action.by, action.terrace, teyuna_shared.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
        game.phase = teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    else:
        game.phase = teyuna_shared.GamePhaseName.SECOND_PLACEMENT
    return teyuna_shared.PlacedBuildingsResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        settlement=action.terrace,
        path=action.path,
        next_player=game.active_player,
    )
