import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    phase.on_enter(game)

    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.AdvancePhaseAction(),
            ),
        )


def test_raises_invalid_action_if_not_buy_or_advance(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    phase.on_enter(game)
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.BuildTerraceAction(
                    coordinate=entities.Coordinate(q=0, r=0, d=0)
                ),
            ),
        )


def test_buy_wisdom_card_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    game.players[game.active_player].resources.update(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.BuyWisdomCardAction(),
        ),
    )
    assert result.finished is False
    assert game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] == 1


def test_advance_phase_finishes(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )
    assert result.finished is True


def test_on_exit_returns_dice_roll_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    assert phase.on_exit(game).next is phases.GamePhaseName.DICE_ROLL


@pytest.fixture
def phase() -> phases.PreDiceRollPhase:
    return phases.PreDiceRollPhase()
