import collections
import random

from ... import player
from ... import entities
from .. import _registry
from . import _placement


class MoveConquistatorAction(_registry.PlayerAction):
    q: int
    r: int
    from_player: player.Nickname | None = None


class MovedConquistatorResult(_registry.ActionExecutionResult):
    q: int = -1
    r: int = -1
    from_player: player.Nickname | None = None
    stolen: entities.ResourceCard | None = None


def handle_dice_play_warrior(
    game: entities.Game, action: MoveConquistatorAction
) -> MovedConquistatorResult:
    previous_phase = game.phase
    error, stolen = _apply_move_conquistator(game, action)
    if error is not None:
        return MovedConquistatorResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.DICE_ROLL
    return MovedConquistatorResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        q=action.q,
        r=action.r,
        from_player=action.from_player,
        stolen=stolen,
    )


def handle_move_conquistator(
    game: entities.Game, action: MoveConquistatorAction
) -> MovedConquistatorResult:
    previous_phase = game.phase
    error, stolen = _apply_move_conquistator(game, action)
    if error is not None:
        return MovedConquistatorResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return MovedConquistatorResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        q=action.q,
        r=action.r,
        from_player=action.from_player,
        stolen=stolen,
    )


def _apply_move_conquistator(
    game: entities.Game, action: MoveConquistatorAction
) -> tuple[str | None, entities.ResourceCard | None]:
    if game.active_player != action.by:
        return f"Player {action.by} is not in turn", None

    location = entities.HexLocation(q=action.q, r=action.r)
    if location == game.conquistator_location:
        return (
            _placement.format_invalid_conquistator_location(
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
