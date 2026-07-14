import random

import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.DiceRollPhase,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.AdvancePhaseAction(),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.DiceRollPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
            ),
        )


def test_advance_phase_finishes(
    game: entities.ActiveGame,
    phase: phases.DiceRollPhase,
) -> None:
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=None)


def test_on_exit_returns_production_when_sum_is_not_seven(
    game: entities.ActiveGame,
) -> None:
    phase = phases.DiceRollPhase(rnd=_FixedRandom(1, 2))
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.PRODUCTION
    assert outcome.value == phases.DiceRollResult(first=1, second=2)
    assert game.last_dice_roll == 3


def test_on_exit_returns_discard_cards_when_sum_is_seven(
    game: entities.ActiveGame,
) -> None:
    phase = phases.DiceRollPhase(rnd=_FixedRandom(2, 5))
    outcome = phase.on_exit(game)
    assert outcome.next is phases.GamePhaseName.DISCARD_CARDS
    assert outcome.value == phases.DiceRollResult(first=2, second=5)
    assert game.last_dice_roll == 7


@pytest.fixture
def phase() -> phases.DiceRollPhase:
    return phases.DiceRollPhase()


class _FixedRandom(random.Random):
    def __init__(self, *values: int) -> None:
        super().__init__()
        self._values = iter(values)

    def randint(self, a: int, b: int) -> int:
        return next(self._values)
