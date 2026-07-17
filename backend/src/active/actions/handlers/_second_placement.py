from ... import entities
from .. import _registry
from . import _errors, _first_placement, _placement


def handle_second_placement(
    game: entities.ActiveGame, action: _first_placement.FreePlacementAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        raise _errors.InvalidSettlementLocation(
            f"Cannot add free terrace at {action.terrace}"
        )

    can = _placement.can_add_free_path_at(
        target=action.path,
        free_edges=game.free_edges,
        existing_settlements={
            *game.players[action.by].settlements.locations(),
            action.terrace,
        },
        existing_paths=game.players[action.by].paths,
        free_vertices=game.free_verticies,
    )
    if not can:
        raise _errors.InvalidPathLocation(f"Cannot add free path at {action.path}")

    game.use_vertex(action.by, action.terrace, entities.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)

    if game.player_idx > 0:
        game.player_idx -= 1
        return _registry.GamePhaseName.SECOND_PLACEMENT
    return _registry.GamePhaseName.DICE_ROLL
