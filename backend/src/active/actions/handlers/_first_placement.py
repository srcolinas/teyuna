import dataclasses

from ... import entities
from .. import _registry, _results
from . import _errors, _placement


@dataclasses.dataclass(frozen=True, slots=True)
class FreePlacementAction(_registry.PlayerAction):
    terrace: entities.Coordinate
    path: entities.Coordinate

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "terrace",
            entities.canonical_vertex(self.terrace.q, self.terrace.r, self.terrace.d),
        )
        object.__setattr__(
            self,
            "path",
            entities.canonical_edge(self.path.q, self.path.r, self.path.d),
        )


def handle_first_placement(
    game: entities.ActiveGame, action: FreePlacementAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
        )

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        return _results.fail(
            _errors.InvalidSettlementLocation(
                target=action.terrace,
                player=action.by,
                free_vertices=game.free_verticies,
                restricted_vertices=game.restricted_verticies,
            )
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
        return _results.fail(
            _errors.InvalidPathLocation(
                target=action.path,
                player=action.by,
                existing_settlements=player_state.settlements.locations(),
                existing_paths=player_state.paths,
                free_edges=game.free_edges,
            )
        )

    game.use_vertex(action.by, action.terrace, entities.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
        return _results.ok(_registry.GamePhaseName.FIRST_PLACEMENT)
    return _results.ok(_registry.GamePhaseName.SECOND_PLACEMENT)
