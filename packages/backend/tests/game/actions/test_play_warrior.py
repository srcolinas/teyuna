from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_shared


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_dice_play_warrior(
        game,
        teyuna_shared.MoveConquistatorAction(by=other, q=1, r=0),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.q == -1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None


def test_raises_when_location_is_unchanged(game: entities.Game) -> None:
    location = game.conquistator_location
    player = game.active_player
    expected = _placement.format_invalid_conquistator_location(
        target=location,
        player=player,
        current_location=location,
    )
    result = actions.handle_dice_play_warrior(
        game,
        teyuna_shared.MoveConquistatorAction(by=player, q=location.q, r=location.r),
    )
    assert result.error == expected
    assert result.q == -1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None


def test_moves_conquistator_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player

    result = actions.handle_dice_play_warrior(
        game,
        teyuna_shared.MoveConquistatorAction(by=player, q=1, r=-1),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == teyuna_shared.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_moves_conquistator_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player

    result = actions.handle_move_conquistator(
        game,
        teyuna_shared.MoveConquistatorAction(by=player, q=1, r=-1),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == teyuna_shared.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_does_not_take_resources_when_from_player_is_none(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_shared.ResourceCard.WOOD] = 2

    result = actions.handle_dice_play_warrior(
        game,
        teyuna_shared.MoveConquistatorAction(by=player, q=1, r=0, from_player=None),
    )

    assert result.error is None
    assert result.q == 1
    assert result.r == 0
    assert result.from_player is None
    assert result.stolen is None
    assert game.players[other].resources[teyuna_shared.ResourceCard.WOOD] == 2
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 0


def test_takes_one_resource_when_from_player_is_set(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_shared.ResourceCard.WOOD] = 2

    result = actions.handle_dice_play_warrior(
        game,
        teyuna_shared.MoveConquistatorAction(by=player, q=1, r=0, from_player=other),
    )

    assert result.error is None
    assert result.q == 1
    assert result.r == 0
    assert result.from_player == other
    assert result.stolen is teyuna_shared.ResourceCard.WOOD
    assert game.players[other].resources[teyuna_shared.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 1
