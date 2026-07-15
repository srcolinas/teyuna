import pytest

from src.active import entities
from src.active.services import phases


def test_any_action_is_rejected(
    game: entities.ActiveGame,
    phase: phases.EndPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.AdvancePhaseAction(),
            ),
        )


def test_on_exit_raises(
    game: entities.ActiveGame,
    phase: phases.EndPhase,
) -> None:
    with pytest.raises(RuntimeError, match="cannot be exited"):
        phase.on_exit(game)


def test_on_enter_is_noop(
    game: entities.ActiveGame,
    phase: phases.EndPhase,
) -> None:
    assert phase.on_enter(game) == phases.EnterOutcome(value=None)


@pytest.fixture
def phase() -> phases.EndPhase:
    return phases.EndPhase()
