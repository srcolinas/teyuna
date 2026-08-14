import teyuna_core

from ... import entities
from .. import _execution
from . import _placement, _longest_road, _victory


def handle_dice_play_pathfinder(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayPathfinderAction,
) -> teyuna_core.PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, context, action)
    if error is not None:
        return teyuna_core.PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, context.by, teyuna_core.GamePhaseName.DICE_ROLL
    )
    return teyuna_core.PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def handle_trade_and_build_play_pathfinder(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayPathfinderAction,
) -> teyuna_core.PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, context, action)
    if error is not None:
        return teyuna_core.PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, context.by, teyuna_core.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_core.PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def _apply_pathfinder(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayPathfinderAction,
) -> tuple[str | None, tuple[teyuna_core.Coordinate, ...]]:
    if game.active_player != context.by:
        return f"Player {context.by} is not in turn", ()

    player_state = game.players[context.by]
    remaining = teyuna_core.MAX_PATHS - len(player_state.paths)
    to_place = action.paths[:remaining]
    placed: list[teyuna_core.Coordinate] = []

    for path in to_place:
        can = _placement.can_add_free_path_at(
            target=path,
            free_edges=game.free_edges,
            existing_settlements=player_state.settlements.locations(),
            existing_paths=player_state.paths,
            free_vertices=game.free_verticies,
        )
        if not can:
            return (
                _placement.format_invalid_path_location(
                    target=path,
                    player=context.by,
                ),
                (),
            )
        game.use_edge(context.by, path)
        _longest_road.update_longest_road(game, context.by, edge=path)
        placed.append(path)
    return None, tuple(placed)
