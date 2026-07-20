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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class MovedConquistatorResult(_registry.ActionExecutionResult):
    q: int = -1
    r: int = -1
    from_player: player.Nickname | None = None
    stolen: entities.ResourceCard | None = None


def handle_dice_play_warrior(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> MovedConquistatorResult:
    error, stolen = _apply_move_conquistator(game, action)
    if error is not None:
        return MovedConquistatorResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return MovedConquistatorResult(
        succeeded=True,
        phase=_registry.GamePhaseName.DICE_ROLL,
        q=action.q,
        r=action.r,
        from_player=action.from_player,
        stolen=stolen,
    )


def handle_move_conquistator(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> MovedConquistatorResult:
    error, stolen = _apply_move_conquistator(game, action)
    if error is not None:
        return MovedConquistatorResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=error,
        )
    return MovedConquistatorResult(
        succeeded=True,
        phase=_registry.GamePhaseName.TRADE_AND_BUILD,
        q=action.q,
        r=action.r,
        from_player=action.from_player,
        stolen=stolen,
    )


def _apply_move_conquistator(
    game: entities.ActiveGame, action: MoveConquistatorAction
) -> tuple[Exception | None, entities.ResourceCard | None]:
    if game.active_player != action.by:
        return (
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn"),
            None,
        )

    location = entities.HexLocation(q=action.q, r=action.r)
    if location == game.conquistator_location:
        return (
            _errors.InvalidConquistatorLocation(
                target=location,
                player=action.by,
                current_location=game.conquistator_location,
            ),
            None,
        )

    game.conquistator_location = location

    stolen: entities.ResourceCard | None = None
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
    return None, stolen
