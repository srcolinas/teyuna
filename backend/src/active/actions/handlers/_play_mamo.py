import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayMamoAction(_registry.PlayerAction):
    resource: entities.ResourceCard


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class PlayedMamoResult(_registry.ActionExecutionResult):
    resource: entities.ResourceCard | None = None


def handle_dice_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> PlayedMamoResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedMamoResult(
        succeeded=True,
        phase=_registry.GamePhaseName.DICE_ROLL,
        resource=action.resource,
    )


def handle_trade_and_build_play_mamo(
    game: entities.ActiveGame, action: PlayMamoAction
) -> PlayedMamoResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedMamoResult(
        succeeded=True,
        phase=_registry.GamePhaseName.TRADE_AND_BUILD,
        resource=action.resource,
    )


def _apply_mamo(game: entities.ActiveGame, action: PlayMamoAction) -> Exception | None:
    if game.active_player != action.by:
        return _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    game.monopoly_of_resource(action.resource)
    return None
