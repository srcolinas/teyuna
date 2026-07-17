import collections
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


def test_rolls_seven_with_no_discards_moves_to_move_conquistator(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([3, 4])),
    )

    assert phase is actions.GamePhaseName.MOVE_CONQUISTATOR
    assert game.to_discard_resources == {}
    assert game.player_idx == 0
    assert game.active_player == player


def test_rolls_seven_with_players_over_seven_moves_to_discard_resources(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player
    over_limit = game.turn_order[1]
    under_limit = game.turn_order[2]
    game.players[over_limit].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 8}
    )
    game.players[under_limit].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 7}
    )

    phase = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([3, 4])),
    )

    assert phase is actions.GamePhaseName.DISCARD_RESOURCES
    assert game.to_discard_resources == {over_limit: 4}


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
