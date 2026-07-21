from src.game import actions, entities


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    result = actions.handle_dice_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=game.turn_order[1],
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
        ),
    )
    assert result.succeeded is False
    assert result.resources is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    result = actions.handle_trade_and_build_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=game.turn_order[1],
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
        ),
    )
    assert result.succeeded is False
    assert result.resources is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_raises_when_supply_lacks_requested_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[entities.ResourceCard.WOOD] = 0

    result = actions.handle_dice_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
        ),
    )
    assert result.succeeded is False
    assert result.resources is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourceSupplyError


def test_raises_when_supply_lacks_duplicate_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[entities.ResourceCard.WOOD] = 1

    result = actions.handle_dice_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.WOOD),
        ),
    )
    assert result.succeeded is False
    assert result.resources is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourceSupplyError


def test_takes_from_supply_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[entities.ResourceCard.WOOD]
    before_stone = game.resource_supply[entities.ResourceCard.STONE]

    resources = (entities.ResourceCard.WOOD, entities.ResourceCard.STONE)
    result = actions.handle_dice_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=resources,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is entities.GamePhaseName.DICE_ROLL
    assert result.resources == resources
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.STONE] == 1
    assert game.resource_supply[entities.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[entities.ResourceCard.STONE] == before_stone - 1


def test_takes_from_supply_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[entities.ResourceCard.WOOD]
    before_stone = game.resource_supply[entities.ResourceCard.STONE]

    resources = (entities.ResourceCard.WOOD, entities.ResourceCard.STONE)
    result = actions.handle_trade_and_build_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=resources,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.resources == resources
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.STONE] == 1
    assert game.resource_supply[entities.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[entities.ResourceCard.STONE] == before_stone - 1
