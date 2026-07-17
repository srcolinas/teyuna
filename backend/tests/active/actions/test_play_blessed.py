import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_dice_play_blessed(
            game,
            actions.PlayBlessedAction(
                by=game.turn_order[1],
                resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
            ),
        )


def test_raises_when_supply_lacks_requested_resource(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.resource_supply[entities.ResourceCard.WOOD] = 0

    with pytest.raises(actions.InsufficientResourceSupplyError):
        actions.handle_dice_play_blessed(
            game,
            actions.PlayBlessedAction(
                by=player,
                resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
            ),
        )


def test_raises_when_supply_lacks_duplicate_resource(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.resource_supply[entities.ResourceCard.WOOD] = 1

    with pytest.raises(actions.InsufficientResourceSupplyError):
        actions.handle_dice_play_blessed(
            game,
            actions.PlayBlessedAction(
                by=player,
                resources=(entities.ResourceCard.WOOD, entities.ResourceCard.WOOD),
            ),
        )


def test_takes_from_supply_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[entities.ResourceCard.WOOD]
    before_stone = game.resource_supply[entities.ResourceCard.STONE]

    phase = actions.handle_dice_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
        ),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.STONE] == 1
    assert game.resource_supply[entities.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[entities.ResourceCard.STONE] == before_stone - 1


def test_takes_from_supply_and_returns_to_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[entities.ResourceCard.WOOD]
    before_stone = game.resource_supply[entities.ResourceCard.STONE]

    phase = actions.handle_trade_and_build_play_blessed(
        game,
        actions.PlayBlessedAction(
            by=player,
            resources=(entities.ResourceCard.WOOD, entities.ResourceCard.STONE),
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.STONE] == 1
    assert game.resource_supply[entities.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[entities.ResourceCard.STONE] == before_stone - 1
