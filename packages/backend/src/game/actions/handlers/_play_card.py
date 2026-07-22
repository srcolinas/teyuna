import teyuna_shared

from ... import entities
from . import _victory

_MIN_BIGGEST_ARMY: int = 3


def play_wisdom_card(
    game: entities.Game,
    action: teyuna_shared.PlayWisdomCardAction,
    *,
    card_phases: dict[teyuna_shared.WisdomCard, teyuna_shared.GamePhaseName],
    phase_label: str,
) -> teyuna_shared.PlayedWisdomCardResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if game.players[action.by].cards[action.card] <= 0:
        return teyuna_shared.PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} does not have card {action.card.value}",
        )

    next_phase = card_phases.get(action.card)
    if next_phase is None:
        return teyuna_shared.PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=(
                f"Card '{action.card.value}' cannot be played during the "
                f"{phase_label} phase."
            ),
        )

    game.use_card(action.by, action.card)
    if action.card is teyuna_shared.WisdomCard.WARRIOR:
        _update_biggest_army(game, action.by)
    if action.card is teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS:
        game.phase = _victory.phase_after_victory_check(game, action.by, next_phase)
        return teyuna_shared.PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            card=action.card,
        )
    game.phase = next_phase
    return teyuna_shared.PlayedWisdomCardResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        card=action.card,
    )


def _update_biggest_army(
    game: entities.Game,
    by: str,
    /,
) -> None:
    """Update biggest army after ``by`` plays a warrior."""
    count = game.players[by].played_cards[teyuna_shared.WisdomCard.WARRIOR]
    if count < _MIN_BIGGEST_ARMY:
        return

    _, stored = game.biggest_army
    # Strictly more than the stored record — including an unassigned tie count.
    if count > stored:
        game.biggest_army = (by, count)
