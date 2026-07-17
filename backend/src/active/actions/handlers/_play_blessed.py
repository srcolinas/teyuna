import collections
import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayBlessedAction(_registry.PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


def handle_dice_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> _registry.GamePhaseName:
    _apply_blessed(game, action)
    return _registry.GamePhaseName.DICE_ROLL


def handle_trade_and_build_play_blessed(
    game: entities.ActiveGame, action: PlayBlessedAction
) -> _registry.GamePhaseName:
    _apply_blessed(game, action)
    return _registry.GamePhaseName.TRADE_AND_BUILD


def _apply_blessed(game: entities.ActiveGame, action: PlayBlessedAction) -> None:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    amount = collections.Counter(action.resources)
    for resource, count in amount.items():
        if game.resource_supply[resource] < count:
            raise _errors.InsufficientResourceSupplyError(
                f"Not enough {resource.value} in the supply"
            )

    game.take_from_supply(to=action.by, amount=amount)
