import random
from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    action = teyuna_core.MoveConquistatorAction(q=1, r=0)
    result = actions.handle_dice_play_warrior(
        game,
        actions.ExecutionContext(by=other, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
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
    action = teyuna_core.MoveConquistatorAction(q=location.q, r=location.r)
    result = actions.handle_dice_play_warrior(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.q == -1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None


def test_moves_conquistator_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player

    action = teyuna_core.MoveConquistatorAction(q=1, r=-1)
    result = actions.handle_dice_play_warrior(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == teyuna_core.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_moves_conquistator_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player

    action = teyuna_core.MoveConquistatorAction(q=1, r=-1)
    result = actions.handle_move_conquistator(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == teyuna_core.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_does_not_take_resources_when_from_player_is_none(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_core.ResourceCard.WOOD] = 2

    action = teyuna_core.MoveConquistatorAction(q=1, r=0, from_player=None)
    result = actions.handle_dice_play_warrior(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.q == 1
    assert result.r == 0
    assert result.from_player is None
    assert result.stolen is None
    assert game.players[other].resources[teyuna_core.ResourceCard.WOOD] == 2
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 0


def test_takes_one_resource_when_from_player_is_set(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_core.ResourceCard.WOOD] = 2

    action = teyuna_core.MoveConquistatorAction(q=1, r=0, from_player=other)
    result = actions.handle_dice_play_warrior(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.q == 1
    assert result.r == 0
    assert result.from_player == other
    assert result.stolen is teyuna_core.ResourceCard.WOOD
    assert game.players[other].resources[teyuna_core.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 1
