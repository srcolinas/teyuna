import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_dice_roll(
            game,
            actions.PlayerAction(by=game.turn_order[1]),
        )


def test_advances_player_idx_and_stays_in_dice_roll(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.player_idx == 1
    assert game.active_player == game.turn_order[1]


def test_wraps_to_first_player_after_last_player(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    player = game.active_player

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.player_idx == 0
    assert game.active_player == game.turn_order[0]
