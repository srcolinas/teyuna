import dataclasses

from .... import player
from ... import entities
from .. import _registry
from . import _errors

_MIN_BIGGEST_ARMY: int = 3


@dataclasses.dataclass(frozen=True, slots=True)
class PlayWisdomCardAction(_registry.PlayerAction):
    card: entities.WisdomCard


def play_wisdom_card(
    game: entities.ActiveGame,
    action: PlayWisdomCardAction,
    *,
    card_phases: dict[entities.WisdomCard, _registry.GamePhaseName],
    phase_label: str,
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    if game.players[action.by].cards[action.card] <= 0:
        raise _errors.PlayerDoesNotHaveCardError(
            f"Player {action.by} does not have card {action.card.value}"
        )

    next_phase = card_phases.get(action.card)
    if next_phase is None:
        raise _registry.ActionNotAllowedError(
            f"Card '{action.card.value}' cannot be played during the {phase_label} phase."
        )

    game.use_card(action.by, action.card)
    if action.card is entities.WisdomCard.WARRIOR:
        _update_biggest_army(game, action.by)
    return next_phase


def _update_biggest_army(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
) -> None:
    """Update biggest army after ``by`` plays a warrior."""
    count = game.players[by].played_cards[entities.WisdomCard.WARRIOR]
    if count < _MIN_BIGGEST_ARMY:
        return

    holder, stored = game.biggest_army
    # Strictly more than the stored record — including an unassigned tie count.
    if count > stored:
        game.biggest_army = (by, count)
