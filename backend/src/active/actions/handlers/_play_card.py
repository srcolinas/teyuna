import dataclasses

from ... import entities
from .. import _registry
from . import _errors


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
    return next_phase
