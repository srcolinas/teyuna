import pytest

from src.active import entities


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.WOOD: 1,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 0,
        },
    ],
)
def test_cannot_buy_path_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(resources)
    with pytest.raises(entities.InsufficientResources):
        game.buy_path(nickname, q=0, r=0, direction=1)


def test_can_buy_path_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game.buy_path(nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game.buy_path(nickname, q=0, r=0, direction=0)
    assert entities.Coordinate(q=0, r=0, d=0) in game.players[nickname].paths


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game.buy_path(nickname, q=0, r=0, direction=0)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0


def test_player_not_in_turn_cannot_buy_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(entities.PlayerNotInTurn):
        game.buy_path(nickname, q=0, r=0, direction=0)
