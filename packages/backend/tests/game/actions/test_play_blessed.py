from src.game import actions, entities
import teyuna_shared


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_dice_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=other,
            resources=(
                teyuna_shared.ResourceCard.WOOD,
                teyuna_shared.ResourceCard.STONE,
            ),
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.resources is None


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_trade_and_build_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=other,
            resources=(
                teyuna_shared.ResourceCard.WOOD,
                teyuna_shared.ResourceCard.STONE,
            ),
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.resources is None


def test_raises_when_supply_lacks_requested_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[teyuna_shared.ResourceCard.WOOD] = 0

    result = actions.handle_dice_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=player,
            resources=(
                teyuna_shared.ResourceCard.WOOD,
                teyuna_shared.ResourceCard.STONE,
            ),
        ),
    )
    assert result.error == "Not enough wood in the supply"
    assert result.resources is None


def test_raises_when_supply_lacks_duplicate_resource(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.resource_supply[teyuna_shared.ResourceCard.WOOD] = 1

    result = actions.handle_dice_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=player,
            resources=(
                teyuna_shared.ResourceCard.WOOD,
                teyuna_shared.ResourceCard.WOOD,
            ),
        ),
    )
    assert result.error == "Not enough wood in the supply"
    assert result.resources is None


def test_takes_from_supply_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[teyuna_shared.ResourceCard.WOOD]
    before_stone = game.resource_supply[teyuna_shared.ResourceCard.STONE]

    resources = (teyuna_shared.ResourceCard.WOOD, teyuna_shared.ResourceCard.STONE)
    result = actions.handle_dice_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=player,
            resources=resources,
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert result.resources == resources
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_shared.ResourceCard.STONE] == 1
    assert game.resource_supply[teyuna_shared.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[teyuna_shared.ResourceCard.STONE] == before_stone - 1


def test_takes_from_supply_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    before_wood = game.resource_supply[teyuna_shared.ResourceCard.WOOD]
    before_stone = game.resource_supply[teyuna_shared.ResourceCard.STONE]

    resources = (teyuna_shared.ResourceCard.WOOD, teyuna_shared.ResourceCard.STONE)
    result = actions.handle_trade_and_build_play_blessed(
        game,
        teyuna_shared.PlayBlessedAction(
            by=player,
            resources=resources,
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.resources == resources
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 1
    assert game.players[player].resources[teyuna_shared.ResourceCard.STONE] == 1
    assert game.resource_supply[teyuna_shared.ResourceCard.WOOD] == before_wood - 1
    assert game.resource_supply[teyuna_shared.ResourceCard.STONE] == before_stone - 1
