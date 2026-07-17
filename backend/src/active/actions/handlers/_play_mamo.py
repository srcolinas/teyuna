import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayMamoAction(_registry.PlayerAction):
    resource: entities.ResourceCard


def handle_dice_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> _registry.GamePhaseName:
    _apply_mamo(game, action)
    return _registry.GamePhaseName.DICE_ROLL


def handle_trade_and_build_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> _registry.GamePhaseName:
    _apply_mamo(game, action)
    return _registry.GamePhaseName.TRADE_AND_BUILD


def _apply_mamo(game: entities.ActiveGame, action: PlayMamoAction) -> None:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    game.monopoly_of_resource(action.resource)
