from src.game import actions, entities
import teyuna_shared


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_dice_play_mamo(
        game,
        teyuna_shared.PlayMamoAction(
            by=other,
            resource=teyuna_shared.ResourceCard.WOOD,
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.resource is None


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_trade_and_build_play_mamo(
        game,
        teyuna_shared.PlayMamoAction(
            by=other,
            resource=teyuna_shared.ResourceCard.WOOD,
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.resource is None


def test_monopolizes_resource_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_shared.ResourceCard.WOOD] = 3

    result = actions.handle_dice_play_mamo(
        game,
        teyuna_shared.PlayMamoAction(
            by=player, resource=teyuna_shared.ResourceCard.WOOD
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert result.resource is teyuna_shared.ResourceCard.WOOD
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 3
    assert game.players[other].resources[teyuna_shared.ResourceCard.WOOD] == 0


def test_monopolizes_resource_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[teyuna_shared.ResourceCard.WOOD] = 3

    result = actions.handle_trade_and_build_play_mamo(
        game,
        teyuna_shared.PlayMamoAction(
            by=player, resource=teyuna_shared.ResourceCard.WOOD
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.resource is teyuna_shared.ResourceCard.WOOD
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 3
    assert game.players[other].resources[teyuna_shared.ResourceCard.WOOD] == 0
