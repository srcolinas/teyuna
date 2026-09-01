import random
from src.game import actions, entities
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    action = teyuna_core.PlayMamoAction(
        resource=teyuna_core.ResourceCard.WOOD,
    )
    result = actions.handle_dice_play_mamo(
        game,
        actions.ExecutionContext(by=other, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.resource is None


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    action = teyuna_core.PlayMamoAction(
        resource=teyuna_core.ResourceCard.WOOD,
    )
    result = actions.handle_trade_and_build_play_mamo(
        game,
        actions.ExecutionContext(by=other, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.resource is None


def test_monopolizes_resource_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_core.ResourceCard.WOOD] = 3

    action = teyuna_core.PlayMamoAction(resource=teyuna_core.ResourceCard.WOOD)
    result = actions.handle_dice_play_mamo(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.resource is teyuna_core.ResourceCard.WOOD
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 3
    assert game.players[other].resources[teyuna_core.ResourceCard.WOOD] == 0


def test_monopolizes_resource_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_core.ResourceCard.WOOD] = 3

    action = teyuna_core.PlayMamoAction(resource=teyuna_core.ResourceCard.WOOD)
    result = actions.handle_trade_and_build_play_mamo(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.resource is teyuna_core.ResourceCard.WOOD
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 3
    assert game.players[other].resources[teyuna_core.ResourceCard.WOOD] == 0
