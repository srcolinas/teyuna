import dataclasses

from ... import entities
from .. import _registry
from . import _errors, _placement
from ._longest_road import update_longest_road
from ._victory import phase_after_victory_check


@dataclasses.dataclass(frozen=True, slots=True)
class PlayPathfinderAction(_registry.PlayerAction):
    paths: tuple[entities.Coordinate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "paths",
            tuple(
                entities.canonical_edge(path.q, path.r, path.d) for path in self.paths
            ),
        )


class PlayedPathfinderResult(_registry.ActionExecutionResult):
    paths: tuple[entities.Coordinate, ...] = ()


def handle_dice_play_pathfinder(
    game: entities.ActiveGame, action: PlayPathfinderAction
) -> PlayedPathfinderResult:
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return PlayedPathfinderResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedPathfinderResult(
        succeeded=True,
        phase=phase_after_victory_check(
            game, action.by, _registry.GamePhaseName.DICE_ROLL
        ),
        paths=placed,
    )


def handle_trade_and_build_play_pathfinder(
    game: entities.ActiveGame, action: PlayPathfinderAction
) -> PlayedPathfinderResult:
    error, placed = _apply_pathfinder(game, action)
    if error is not None:
        return PlayedPathfinderResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedPathfinderResult(
        succeeded=True,
        phase=phase_after_victory_check(
            game, action.by, _registry.GamePhaseName.TRADE_AND_BUILD
        ),
        paths=placed,
    )


def _apply_pathfinder(
    game: entities.ActiveGame, action: PlayPathfinderAction
) -> tuple[Exception | None, tuple[entities.Coordinate, ...]]:
    if game.active_player != action.by:
        return (
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn"),
            (),
        )

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
                _errors.InvalidPathLocation(
                    target=path,
                    player=action.by,
                    existing_settlements=player_state.settlements.locations(),
                    existing_paths=player_state.paths,
                    free_edges=game.free_edges,
                ),
                (),
            )
        game.use_edge(action.by, path)
        update_longest_road(game, action.by, edge=path)
        placed.append(path)
    return None, tuple(placed)
