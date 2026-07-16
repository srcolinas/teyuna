import dataclasses

from ... import entities, validations
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class FirstPlacementAction(_registry.PlayerAction):
    terrace: entities.Coordinate
    path: entities.Coordinate


def handle_first_placement(
    game: entities.ActiveGame, action: FirstPlacementAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    can, blocked = validations.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        raise _errors.InvalidSettlementLocation(
            f"Cannot add free terrace at {action.terrace}"
        )

    can = validations.can_add_free_path_at(
        target=action.path,
        neighbor_terrace=action.terrace,
        free_edges=game.free_edges,
    )
    if not can:
        raise _errors.InvalidPathLocation(f"Cannot add free path at {action.path}")

    game.free_verticies -= blocked
    game.restricted_verticies.update(blocked)
    game.free_edges.remove(action.path)
    game.players[action.by].paths.add(action.path)
    game.players[action.by].settlements[action.terrace] = (
        entities.SettlementType.TERRACE
    )
    if game.player_idx < len(game.players) - 1:
        game.player_idx += 1
    return _registry.GamePhaseName.FIRST_PLACEMENT
