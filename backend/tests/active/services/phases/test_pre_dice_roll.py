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


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    phase.on_enter(game)
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.BuyAction(
                    item=phases.Buyable.TERRACE,
                    coordinate=entities.Coordinate(q=0, r=0, d=0),
                ),
            ),
        )


def test_play_warrior_finishes_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=entities.WisdomCard.WARRIOR)
    assert player.played_cards[entities.WisdomCard.WARRIOR] == 1
    assert player.cards[entities.WisdomCard.WARRIOR] == 0
    assert game.warrior_return_phase == phases.GamePhaseName.PRE_DICE_ROLL.value


def test_play_blessing_finishes_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(
                card=entities.WisdomCard.BLESSING_OF_ALUNA
            ),
        ),
    )
    assert result == phases.RunOutcome(
        finished=True, value=entities.WisdomCard.BLESSING_OF_ALUNA
    )
    assert player.played_cards[entities.WisdomCard.BLESSING_OF_ALUNA] == 1
    assert player.cards[entities.WisdomCard.BLESSING_OF_ALUNA] == 0
    assert game.blessing_return_phase == phases.GamePhaseName.PRE_DICE_ROLL.value


def test_play_non_interrupt_wisdom_keeps_phase_open(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.PATHFINDER] = 1
    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.PATHFINDER),
        ),
    )
    assert result == phases.RunOutcome(
        finished=False, value=entities.WisdomCard.PATHFINDER
    )
    assert player.played_cards[entities.WisdomCard.PATHFINDER] == 1
    assert game.warrior_return_phase is None
    assert game.blessing_return_phase is None


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


def test_on_exit_after_warrior_returns_warrior_move_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
        ),
    )
    assert phase.on_exit(game).next is phases.GamePhaseName.WARRIOR_MOVE_CONQUISTATOR


def test_on_exit_after_blessing_returns_blessing_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.PlayWisdomCardAction(
                card=entities.WisdomCard.BLESSING_OF_ALUNA
            ),
        ),
    )
    assert phase.on_exit(game).next is phases.GamePhaseName.BLESSING_OF_ALUNA


def test_on_exit_returns_dice_roll_phase(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    assert phase.on_exit(game).next is phases.GamePhaseName.DICE_ROLL


def test_on_enter_clears_cards_bought_this_turn(
    game: entities.ActiveGame,
    phase: phases.PreDiceRollPhase,
) -> None:
    player = game.players[game.active_player]
    player.cards_bought_this_turn[entities.WisdomCard.WARRIOR] = 1
    phase.on_enter(game)
    assert player.cards_bought_this_turn[entities.WisdomCard.WARRIOR] == 0


@pytest.fixture
def phase() -> phases.PreDiceRollPhase:
    return phases.PreDiceRollPhase()
