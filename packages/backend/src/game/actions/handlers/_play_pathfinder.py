import teyuna_shared

from ... import entities
from . import _placement, _longest_road, _victory


def handle_dice_play_pathfinder(
    game: entities.Game, action: teyuna_shared.PlayPathfinderAction
) -> teyuna_shared.PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return teyuna_shared.PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, action.by, teyuna_shared.GamePhaseName.DICE_ROLL
    )
    return teyuna_shared.PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def handle_trade_and_build_play_pathfinder(
    game: entities.Game, action: teyuna_shared.PlayPathfinderAction
) -> teyuna_shared.PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return teyuna_shared.PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, action.by, teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    )
    return teyuna_shared.PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def _apply_pathfinder(
    game: entities.Game, action: teyuna_shared.PlayPathfinderAction
) -> tuple[str | None, tuple[teyuna_shared.Coordinate, ...]]:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn", ()

    player_state = game.players[action.by]
    remaining = teyuna_shared.MAX_PATHS - len(player_state.paths)
    to_place = action.paths[:remaining]
    placed: list[teyuna_shared.Coordinate] = []

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
                    player=action.by,
                    existing_settlements=player_state.settlements.locations(),
                    existing_paths=player_state.paths,
                    free_edges=game.free_edges,
                ),
                (),
            )
        game.use_edge(action.by, path)
        _longest_road.update_longest_road(game, action.by, edge=path)
        placed.append(path)
    return None, tuple(placed)
