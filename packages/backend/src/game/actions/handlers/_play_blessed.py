import collections

import teyuna_shared

from ... import entities


def handle_dice_play_blessed(
    game: entities.Game, action: teyuna_shared.PlayBlessedAction
) -> teyuna_shared.PlayedBlessedResult:
    previous_phase = game.phase
    error = _apply_blessed(game, action)
    if error is not None:
        return teyuna_shared.PlayedBlessedResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    return teyuna_shared.PlayedBlessedResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resources=action.resources,
    )


def handle_trade_and_build_play_blessed(
    game: entities.Game, action: teyuna_shared.PlayBlessedAction
) -> teyuna_shared.PlayedBlessedResult:
    previous_phase = game.phase
    error = _apply_blessed(game, action)
    if error is not None:
        return teyuna_shared.PlayedBlessedResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    return teyuna_shared.PlayedBlessedResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resources=action.resources,
    )


def _apply_blessed(
    game: entities.Game, action: teyuna_shared.PlayBlessedAction
) -> str | None:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn"

    amount: collections.Counter[teyuna_shared.ResourceCard] = collections.Counter(
        action.resources
    )
    for resource, count in amount.items():
        if game.resource_supply[resource] < count:
            return f"Not enough {resource.value} in the supply"

    game.take_from_supply(to=action.by, amount=amount)
    return None
