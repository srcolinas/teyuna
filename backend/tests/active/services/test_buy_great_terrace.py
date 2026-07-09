import pytest

from src.active import InsufficientResources, InvalidSettlementLocation, PlayerNotInTurn
from src.active import entities
from src.active.services import (
    add_initial_terrace,
    buy_great_terrace,
    buy_path,
    buy_terrace,
)

from ... import utils


def _fund_path_purchase(
    game: entities.ActiveGame, nickname: str, *, count: int = 1
) -> None:
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: count,
            entities.ResourceCard.WOOD: count,
        }
    )


def test_cannot_buy_great_terrace_if_terrace_not_placed_before(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    with pytest.raises(
        InvalidSettlementLocation,
        match="You must first build a terrace at specified location.",
    ):
        buy_great_terrace(game, nickname, q=0, r=0, direction=2)


def test_can_buy_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    with utils.assert_not_raises(InsufficientResources):
        buy_great_terrace(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.GOLD: 2,
            entities.ResourceCard.MAIZE: 2,
        },
    ],
)
def test_cannot_buy_great_terrace_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(resources)
    with pytest.raises(InsufficientResources):
        buy_great_terrace(game, nickname, q=0, r=0, direction=0)


def test_great_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=2)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=1)
    buy_path(game, nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    buy_great_terrace(game, nickname, q=0, r=0, direction=2)
    assert (
        game.players[nickname].settlements[entities.Coordinate(q=0, r=0, d=2)]
        is entities.SettlementType.GREAT_TERRACE
    )


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    buy_great_terrace(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[nickname].resources[entities.ResourceCard.MAIZE] == 0


def test_player_not_in_turn_cannot_buy_great_terrace(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    game._turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(PlayerNotInTurn):
        buy_great_terrace(game, nickname, q=0, r=0, direction=0)


def test_cannot_buy_great_terrace_if_not_enough_great_terraces_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 300,
            entities.ResourceCard.MAIZE: 200,
            entities.ResourceCard.STONE: 20,
            entities.ResourceCard.WOOD: 20,
            entities.ResourceCard.COTTON: 10,
        }
    )
    add_initial_terrace(game, nickname, q=0, r=-2, direction=0)
    buy_great_terrace(game, nickname, q=0, r=-2, direction=0)
    buy_path(game, nickname, q=0, r=-2, direction=0)
    buy_path(game, nickname, q=1, r=-2, direction=5)
    buy_terrace(game, nickname, q=1, r=-2, direction=0)
    buy_great_terrace(game, nickname, q=1, r=-2, direction=0)
    buy_path(game, nickname, q=1, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=5)
    buy_terrace(game, nickname, q=2, r=-2, direction=0)
    buy_great_terrace(game, nickname, q=2, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=1)
    buy_terrace(game, nickname, q=2, r=-2, direction=2)
    buy_great_terrace(game, nickname, q=2, r=-2, direction=2)
    buy_path(game, nickname, q=2, r=-1, direction=0)
    buy_path(game, nickname, q=2, r=-1, direction=1)
    buy_terrace(game, nickname, q=2, r=-1, direction=2)
    with pytest.raises(InsufficientResources):
        buy_great_terrace(game, nickname, q=2, r=-1, direction=2)
