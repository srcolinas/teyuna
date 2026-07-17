import dataclasses
from typing import Final

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class PlayWisdomCardAction(_registry.PlayerAction):
    card: entities.WisdomCard


def handle_dice_roll(
    game: entities.ActiveGame, action: _registry.PlayerAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    dice_1, dice_2 = action.rng_.randint(1, 6), action.rng_.randint(1, 6)
    total = dice_1 + dice_2

    if total == 7:
        return _registry.GamePhaseName.MOVE_CONQUISTATOR
    return _registry.GamePhaseName.TRADE_AND_BUILD


def handle_play_wisdom_card(
    game: entities.ActiveGame, action: PlayWisdomCardAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    if game.players[action.by].cards[action.card] <= 0:
        raise _errors.PlayerDoesNotHaveCardError(
            f"Player {action.by} does not have card {action.card.value}"
        )

    next_phase = _CARD_PHASES.get(action.card)
    if next_phase is None:
        raise _registry.ActionNotAllowedError(
            f"Card '{action.card.value}' cannot be played during the dice roll phase."
        )

    game.use_card(action.by, action.card)
    return next_phase


_CARD_PHASES: Final[dict[entities.WisdomCard, _registry.GamePhaseName]] = {
    entities.WisdomCard.WARRIOR: _registry.GamePhaseName.DICE_PLAY_WARRIOR,
    entities.WisdomCard.WINDOM_OF_MAMO: _registry.GamePhaseName.DICE_PLAY_MAMO,
    entities.WisdomCard.BLESSING_OF_ALUNA: _registry.GamePhaseName.DICE_PLAY_BLESSED,
    entities.WisdomCard.PATHFINDER: _registry.GamePhaseName.DICE_PLAY_PATHFINDER,
    entities.WisdomCard.LEGACY_OF_THE_ELDERS: _registry.GamePhaseName.DICE_ROLL,
}
