import collections
import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayBlessedAction(_registry.PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayedBlessedResult(_registry.ActionExecutionResult):
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


def handle_dice_play_blessed(
    game: entities.Game, action: PlayBlessedAction
) -> PlayedBlessedResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            succeeded=False,
            phase=game.phase,
            by=action.by,
            due_to_timeout=action.due_to_timeout,
            error=error,
        )
    game.phase = entities.GamePhaseName.DICE_ROLL
    return PlayedBlessedResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
        resources=action.resources,
    )


def handle_trade_and_build_play_blessed(
    game: entities.Game, action: PlayBlessedAction
) -> PlayedBlessedResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            succeeded=False,
            phase=game.phase,
            by=action.by,
            due_to_timeout=action.due_to_timeout,
            error=error,
        )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return PlayedBlessedResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
        resources=action.resources,
    )


def _apply_blessed(game: entities.Game, action: PlayBlessedAction) -> Exception | None:
    if game.active_player != action.by:
        return _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    amount = collections.Counter(action.resources)
    for resource, count in amount.items():
        if game.resource_supply[resource] < count:
            return _errors.InsufficientResourceSupplyError(
                f"Not enough {resource.value} in the supply"
            )

    game.take_from_supply(to=action.by, amount=amount)
    return None
