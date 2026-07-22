import pydantic

from ... import entities
from .. import _registry
from . import _placement, _longest_road, _victory


class PlayPathfinderAction(_registry.PlayerAction):
    paths: tuple[entities.Coordinate, ...]

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "PlayPathfinderAction":
        object.__setattr__(
            self,
            "paths",
            tuple(
                entities.canonical_edge(path.q, path.r, path.d) for path in self.paths
            ),
        )
        return self


class PlayedPathfinderResult(_registry.ActionExecutionResult):
    paths: tuple[entities.Coordinate, ...] = ()


def handle_dice_play_pathfinder(
    game: entities.Game, action: PlayPathfinderAction
) -> PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, action.by, entities.GamePhaseName.DICE_ROLL
    )
    return PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def handle_trade_and_build_play_pathfinder(
    game: entities.Game, action: PlayPathfinderAction
) -> PlayedPathfinderResult:
    previous_phase = game.phase
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return PlayedPathfinderResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = _victory.phase_after_victory_check(
        game, action.by, entities.GamePhaseName.TRADE_AND_BUILD
    )
    return PlayedPathfinderResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        paths=placed,
    )


def _apply_pathfinder(
    game: entities.Game, action: PlayPathfinderAction
) -> tuple[str | None, tuple[entities.Coordinate, ...]]:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn", ()

    player_state = game.players[action.by]
    remaining = entities.MAX_PATHS - len(player_state.paths)
    to_place = action.paths[:remaining]
    placed: list[entities.Coordinate] = []

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
