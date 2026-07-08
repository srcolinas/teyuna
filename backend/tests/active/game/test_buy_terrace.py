import pytest

from src.active import entities

from ... import utils


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 0,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 0,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        },
    ],
)
def test_cannot_buy_terrace_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(resources)
    with pytest.raises(entities.InsufficientResources):
        game.buy_terrace(nickname, q=0, r=0, direction=2)


def test_can_buy_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    with utils.assert_not_raises(entities.InsufficientResources):
        game.buy_terrace(nickname, q=0, r=0, direction=2)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    game.buy_terrace(nickname, q=0, r=0, direction=2)
    assert (
        game.players[nickname].settlements[entities.Coordinate(q=0, r=0, d=2)]
        is entities.SettlementType.TERRACE
    )


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    game.buy_terrace(nickname, q=0, r=0, direction=2)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0
    assert game.players[nickname].resources[entities.ResourceCard.COTTON] == 0
    assert game.players[nickname].resources[entities.ResourceCard.MAIZE] == 0


def test_player_not_in_turn_cannot_buy_terrace(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(entities.PlayerNotInTurn):
        game.buy_terrace(nickname, q=0, r=0, direction=2)


def test_cannot_buy_terrace_if_not_enough_terraces_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=-2, direction=0)
    game.add_path(nickname, q=0, r=-2, direction=0)
    game.add_path(nickname, q=1, r=-2, direction=5)
    game.add_terrace(nickname, q=1, r=-2, direction=0)
    game.add_path(nickname, q=1, r=-2, direction=0)
    game.add_path(nickname, q=2, r=-2, direction=5)
    game.add_terrace(nickname, q=2, r=-2, direction=0)
    game.add_path(nickname, q=2, r=-2, direction=0)
    game.add_path(nickname, q=2, r=-2, direction=1)
    game.add_terrace(nickname, q=2, r=-2, direction=2)
    game.add_path(nickname, q=2, r=-1, direction=0)
    game.add_path(nickname, q=2, r=-1, direction=1)
    game.add_terrace(nickname, q=2, r=-1, direction=2)
    game.add_path(nickname, q=2, r=0, direction=0)
    game.add_path(nickname, q=2, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    with pytest.raises(entities.InsufficientResources):
        game.buy_terrace(nickname, q=2, r=0, direction=2)
