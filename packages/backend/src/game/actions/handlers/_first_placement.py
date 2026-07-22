import pydantic

from ... import player
from ... import entities
from .. import _registry
from . import _placement


class FreePlacementAction(_registry.PlayerAction):
    terrace: entities.Coordinate
    path: entities.Coordinate

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "FreePlacementAction":
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
        return self


class PlacedBuildingsResult(_registry.ActionExecutionResult):
    settlement: entities.Coordinate | None = None
    path: entities.Coordinate | None = None
    next_player: player.Nickname = ""


def handle_first_placement(
    game: entities.Game, action: FreePlacementAction
) -> PlacedBuildingsResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        return PlacedBuildingsResult(
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
        return PlacedBuildingsResult(
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

    game.use_vertex(action.by, action.terrace, entities.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)

    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
        game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    else:
        game.phase = entities.GamePhaseName.SECOND_PLACEMENT
    return PlacedBuildingsResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        settlement=action.terrace,
        path=action.path,
        next_player=game.active_player,
    )
