from src.game import actions, entities
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    action = teyuna_core.PlayBlessedAction(
        by=other,
        resources=(
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.STONE,
        ),
    )
    result = actions.handle_dice_play_blessed(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.resources is None


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    action = teyuna_core.PlayBlessedAction(
        by=other,
        resources=(
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.STONE,
        ),
    )
    result = actions.handle_trade_and_build_play_blessed(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.resources is None


def test_raises_when_supply_lacks_requested_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[teyuna_core.ResourceCard.WOOD] = 0

    action = teyuna_core.PlayBlessedAction(
        by=player,
        resources=(
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.STONE,
        ),
    )
    result = actions.handle_dice_play_blessed(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Not enough wood in the supply"
    assert result.resources is None


def test_raises_when_supply_lacks_duplicate_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[teyuna_core.ResourceCard.WOOD] = 1

    action = teyuna_core.PlayBlessedAction(
        by=player,
        resources=(
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.WOOD,
        ),
    )
    result = actions.handle_dice_play_blessed(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Not enough wood in the supply"
    assert result.resources is None


def test_takes_from_supply_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[teyuna_core.ResourceCard.WOOD]
    before_stone = game.resource_supply[teyuna_core.ResourceCard.STONE]

    resources = (teyuna_core.ResourceCard.WOOD, teyuna_core.ResourceCard.STONE)
    action = teyuna_core.PlayBlessedAction(
        by=player,
        resources=resources,
    )
    result = actions.handle_dice_play_blessed(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.resources == resources
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_core.ResourceCard.STONE] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[teyuna_core.ResourceCard.STONE] == before_stone - 1


def test_takes_from_supply_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[teyuna_core.ResourceCard.WOOD]
    before_stone = game.resource_supply[teyuna_core.ResourceCard.STONE]

    resources = (teyuna_core.ResourceCard.WOOD, teyuna_core.ResourceCard.STONE)
    action = teyuna_core.PlayBlessedAction(
        by=player,
        resources=resources,
    )
    result = actions.handle_trade_and_build_play_blessed(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.resources == resources
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_core.ResourceCard.STONE] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[teyuna_core.ResourceCard.STONE] == before_stone - 1
