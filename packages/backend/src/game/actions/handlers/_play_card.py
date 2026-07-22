from ... import player
from ... import entities
from .. import _registry
from ._victory import phase_after_victory_check

_MIN_BIGGEST_ARMY: int = 3


class PlayWisdomCardAction(_registry.PlayerAction):
    card: entities.WisdomCard


class PlayedWisdomCardResult(_registry.ActionExecutionResult):
    card: entities.WisdomCard | None = None


def play_wisdom_card(
    game: entities.Game,
    action: PlayWisdomCardAction,
    *,
    card_phases: dict[entities.WisdomCard, entities.GamePhaseName],
    phase_label: str,
) -> PlayedWisdomCardResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    if game.players[action.by].cards[action.card] <= 0:
        return PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} does not have card {action.card.value}",
        )

    next_phase = card_phases.get(action.card)
    if next_phase is None:
        return PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=(
                f"Card '{action.card.value}' cannot be played during the "
                f"{phase_label} phase."
            ),
        )

    game.use_card(action.by, action.card)
    if action.card is entities.WisdomCard.WARRIOR:
        _update_biggest_army(game, action.by)
    if action.card is entities.WisdomCard.LEGACY_OF_THE_ELDERS:
        game.phase = phase_after_victory_check(game, action.by, next_phase)
        return PlayedWisdomCardResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            card=action.card,
        )
    game.phase = next_phase
    return PlayedWisdomCardResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        card=action.card,
    )


def _update_biggest_army(
    game: entities.Game,
    by: player.Nickname,
    /,
) -> None:
    """Update biggest army after ``by`` plays a warrior."""
    count = game.players[by].played_cards[entities.WisdomCard.WARRIOR]
    if count < _MIN_BIGGEST_ARMY:
        return

    _, stored = game.biggest_army
    # Strictly more than the stored record — including an unassigned tie count.
    if count > stored:
        game.biggest_army = (by, count)
