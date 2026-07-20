import dataclasses

from ... import entities
from .. import _registry, _results
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayMamoAction(_registry.PlayerAction):
    resource: entities.ResourceCard


def handle_dice_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> _registry.ActionExecutionResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return _results.fail(error)
    return _results.ok(_registry.GamePhaseName.DICE_ROLL)


def handle_trade_and_build_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> _registry.ActionExecutionResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return _results.fail(error)
    return _results.ok(_registry.GamePhaseName.TRADE_AND_BUILD)


def _apply_mamo(game: entities.ActiveGame, action: PlayMamoAction) -> Exception | None:
    if game.active_player != action.by:
        return _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    game.monopoly_of_resource(action.resource)
    return None
