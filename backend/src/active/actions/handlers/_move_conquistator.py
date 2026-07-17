import collections
import dataclasses
import random

from .... import player
from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class MoveConquistatorAction(_registry.PlayerAction):
    q: int
    r: int
    from_player: player.Nickname | None = None


def handle_dice_play_warrior(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> _registry.GamePhaseName:
    _apply_move_conquistator(game, action)
    return _registry.GamePhaseName.DICE_ROLL


def handle_move_conquistator(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> _registry.GamePhaseName:
    _apply_move_conquistator(game, action)
    return _registry.GamePhaseName.TRADE_AND_BUILD


def _apply_move_conquistator(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> None:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    location = entities.HexLocation(q=action.q, r=action.r)
    if location == game.conquistator_location:
        raise _errors.InvalidConquistatorLocation(
            f"Conquistator is already at {location}"
        )

    game.conquistator_location = location

    if action.from_player is not None:
        victim_resources = game.players[action.from_player].resources
        available = [card for card, count in victim_resources.items() if count > 0]
        if available:
            stolen = random.choice(available)
            game.take_resources(
                action.from_player,
                action.by,
                collections.Counter({stolen: 1}),
            )
