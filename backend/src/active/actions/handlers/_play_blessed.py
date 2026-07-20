import collections
import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayBlessedAction(_registry.PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class PlayedBlessedResult(_registry.ActionExecutionResult):
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


def handle_dice_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> PlayedBlessedResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedBlessedResult(
        succeeded=True,
        phase=_registry.GamePhaseName.DICE_ROLL,
        resources=action.resources,
    )


def handle_trade_and_build_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> PlayedBlessedResult:
    error = _apply_blessed(game, action)
    if error is not None:
        return PlayedBlessedResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return PlayedBlessedResult(
        succeeded=True,
        phase=_registry.GamePhaseName.TRADE_AND_BUILD,
        resources=action.resources,
    )


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
