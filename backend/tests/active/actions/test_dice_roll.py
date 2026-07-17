import random

import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_dice_roll(
            game,
            actions.PlayerAction(
                by=game.turn_order[1],
                rng_=FixedRandom([1, 1]),
            ),
        )


def test_rolls_seven_moves_to_move_conquistator(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([3, 4])),
    )

    assert phase is actions.GamePhaseName.MOVE_CONQUISTATOR
    assert game.player_idx == 0
    assert game.active_player == player


def test_rolls_non_seven_moves_to_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([2, 3])),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.player_idx == 0
    assert game.active_player == player


class FixedRandom(random.Random):
    def __init__(self, values: list[int]) -> None:
        super().__init__()
        self._values = iter(values)

    def randint(self, a: int, b: int) -> int:
        value = next(self._values)
        assert a <= value <= b
        return value
