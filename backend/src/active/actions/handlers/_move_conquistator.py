import collections
import random

from ... import entities
from .. import _registry
from . import _errors
from ._dice_play_warrior import MoveConquistatorAction


def handle_move_conquistator(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> _registry.GamePhaseName:
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

    return _registry.GamePhaseName.TRADE_AND_BUILD
