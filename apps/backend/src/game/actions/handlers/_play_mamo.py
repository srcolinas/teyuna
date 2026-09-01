import teyuna_core

from ... import entities
from .. import _execution


def handle_dice_play_mamo(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayMamoAction,
) -> teyuna_core.PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, context, action)
    if error is not None:
        return teyuna_core.PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    return teyuna_core.PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def handle_trade_and_build_play_mamo(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayMamoAction,
) -> teyuna_core.PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, context, action)
    if error is not None:
        return teyuna_core.PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    return teyuna_core.PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def _apply_mamo(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.PlayMamoAction,
) -> str | None:
    if game.active_player != context.by:
        return f"Player {context.by} is not in turn"

    game.monopoly_of_resource(action.resource)
    return None
