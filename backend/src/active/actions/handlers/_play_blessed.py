import collections
import dataclasses

from ... import entities
from .. import _registry, _results
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayBlessedAction(_registry.PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


def handle_dice_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> _registry.ActionExecutionResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return _results.fail(error)
    return _results.ok(_registry.GamePhaseName.DICE_ROLL)


def handle_trade_and_build_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> _registry.ActionExecutionResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return _results.fail(error)
    return _results.ok(_registry.GamePhaseName.TRADE_AND_BUILD)


def _apply_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> Exception | None:
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
