import teyuna_shared

from ... import entities


def handle_dice_play_mamo(
    game: entities.Game, action: teyuna_shared.PlayMamoAction
) -> teyuna_shared.PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, action)
    if error is not None:
        return teyuna_shared.PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    return teyuna_shared.PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def handle_trade_and_build_play_mamo(
    game: entities.Game, action: teyuna_shared.PlayMamoAction
) -> teyuna_shared.PlayedMamoResult:
    previous_phase = game.phase
    error = _apply_mamo(game, action)
    if error is not None:
        return teyuna_shared.PlayedMamoResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    return teyuna_shared.PlayedMamoResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resource=action.resource,
    )


def _apply_mamo(
    game: entities.Game, action: teyuna_shared.PlayMamoAction
) -> str | None:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn"

    game.monopoly_of_resource(action.resource)
    return None
