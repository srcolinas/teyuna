import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.LegacyOfTheEldersPhase,
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
    phase: phases.LegacyOfTheEldersPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(
                    card=entities.WisdomCard.LEGACY_OF_THE_ELDERS
                ),
            ),
        )


def test_advance_phase_finishes(
    game: entities.ActiveGame,
    phase: phases.LegacyOfTheEldersPhase,
) -> None:
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=None)


def test_on_exit_returns_to_legacy_return_phase(
    game: entities.ActiveGame,
    phase: phases.LegacyOfTheEldersPhase,
) -> None:
    game.legacy_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert game.legacy_return_phase is None


def test_on_exit_returns_to_trade_and_build_when_set(
    game: entities.ActiveGame,
    phase: phases.LegacyOfTheEldersPhase,
) -> None:
    game.legacy_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.TRADE_AND_BUILD
    assert game.legacy_return_phase is None


@pytest.fixture
def phase() -> phases.LegacyOfTheEldersPhase:
    return phases.LegacyOfTheEldersPhase()
