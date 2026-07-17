import dataclasses

from ... import entities
from .. import _registry
from . import _errors, _placement


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


def handle_dice_play_pathfinder(
    game: entities.ActiveGame, action: PlayPathfinderAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    player_state = game.players[action.by]
    remaining = entities.MAX_PATHS - len(player_state.paths)
    to_place = action.paths[:remaining]

    for path in to_place:
        can = _placement.can_add_free_path_at(
            target=path,
            free_edges=game.free_edges,
            existing_settlements=player_state.settlements.locations(),
            existing_paths=player_state.paths,
            free_vertices=game.free_verticies,
        )
        if not can:
            raise _errors.InvalidPathLocation(f"Cannot add free path at {path}")
        game.use_edge(action.by, path)

    return _registry.GamePhaseName.DICE_ROLL
