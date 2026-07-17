import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_dice_play_warrior(
            game,
            actions.MoveConquistatorAction(by=game.turn_order[1], q=1, r=0),
        )


def test_moves_conquistator_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    phase = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=-1),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_does_not_take_resources_when_from_player_is_none(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 2

    actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=0, from_player=None),
    )

    assert game.players[other].resources[entities.ResourceCard.WOOD] == 2
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 0


def test_takes_one_resource_when_from_player_is_set(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 2

    actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=0, from_player=other),
    )

    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
