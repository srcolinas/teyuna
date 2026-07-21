import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayMamoAction(_registry.PlayerAction):
    resource: entities.ResourceCard


class PlayedMamoResult(_registry.ActionExecutionResult):
    resource: entities.ResourceCard | None = None


def handle_dice_play_mamo(
    game: entities.Game, action: PlayMamoAction
) -> PlayedMamoResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            succeeded=False,
            phase=game.phase,
            by=action.by,
            due_to_timeout=action.due_to_timeout,
            error=error,
        )
    game.phase = entities.GamePhaseName.DICE_ROLL
    return PlayedMamoResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
        resource=action.resource,
    )


def handle_trade_and_build_play_mamo(
    game: entities.Game, action: PlayMamoAction
) -> PlayedMamoResult:
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            succeeded=False,
            phase=game.phase,
            by=action.by,
            due_to_timeout=action.due_to_timeout,
            error=error,
        )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return PlayedMamoResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
        resource=action.resource,
    )


def _apply_mamo(game: entities.Game, action: PlayMamoAction) -> Exception | None:
    if game.active_player != action.by:
        return _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    game.monopoly_of_resource(action.resource)
    return None
