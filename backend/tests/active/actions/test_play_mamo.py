from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    result = actions.handle_dice_play_mamo(
        game,
        actions.PlayMamoAction(
            by=game.turn_order[1],
            resource=entities.ResourceCard.WOOD,
        ),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_monopolizes_resource_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 3

    result = actions.handle_dice_play_mamo(
        game,
        actions.PlayMamoAction(by=player, resource=entities.ResourceCard.WOOD),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 3
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 0


def test_monopolizes_resource_and_returns_to_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 3

    result = actions.handle_trade_and_build_play_mamo(
        game,
        actions.PlayMamoAction(by=player, resource=entities.ResourceCard.WOOD),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 3
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 0
