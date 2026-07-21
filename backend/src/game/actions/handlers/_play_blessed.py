import collections

from ... import entities
from .. import _registry


class PlayBlessedAction(_registry.PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayedBlessedResult(_registry.ActionExecutionResult):
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


def handle_dice_play_blessed(
    game: entities.Game, action: PlayBlessedAction
) -> PlayedBlessedResult:
    previous_phase = game.phase
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.DICE_ROLL
    return PlayedBlessedResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resources=action.resources,
    )


def handle_trade_and_build_play_blessed(
    game: entities.Game, action: PlayBlessedAction
) -> PlayedBlessedResult:
    previous_phase = game.phase
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return PlayedBlessedResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        resources=action.resources,
    )


def _apply_blessed(game: entities.Game, action: PlayBlessedAction) -> str | None:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn"

    amount = collections.Counter(action.resources)
    for resource, count in amount.items():
        if game.resource_supply[resource] < count:
            return f"Not enough {resource.value} in the supply"

    game.take_from_supply(to=action.by, amount=amount)
    return None
