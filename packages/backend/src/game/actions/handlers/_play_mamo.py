from ... import entities
from .. import _registry


class PlayMamoAction(_registry.PlayerAction):
    resource: entities.ResourceCard


class PlayedMamoResult(_registry.ActionExecutionResult):
    resource: entities.ResourceCard | None = None


def handle_dice_play_mamo(
    game: entities.Game, action: PlayMamoAction
) -> PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.DICE_ROLL
    return PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def handle_trade_and_build_play_mamo(
    game: entities.Game, action: PlayMamoAction
) -> PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, action)
    if error is not None:
        return PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def _apply_mamo(game: entities.Game, action: PlayMamoAction) -> str | None:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn"

    game.monopoly_of_resource(action.resource)
    return None
