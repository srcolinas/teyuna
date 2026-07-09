import itertools

import pytest

from src.active import InsufficientResources, InvalidSettlementLocation, PlayerNotInTurn
from src.active import entities
from src.active.services import add_initial_terrace, buy_path, buy_terrace

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
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(resources)
    with pytest.raises(InsufficientResources):
        buy_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_needs_to_be_connected_to_a_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    _fund_terrace_purchase(game, nickname)
    with pytest.raises(InvalidSettlementLocation):
        buy_terrace(game, nickname, q=0, r=0, direction=0)


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    with utils.assert_not_raises(Exception):
        buy_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_cannot_be_added_by_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    game._turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(PlayerNotInTurn):
        buy_terrace(game, nickname, q=0, r=0, direction=2)


def test_can_buy_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    with utils.assert_not_raises(InsufficientResources):
        buy_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    buy_terrace(game, nickname, q=0, r=0, direction=2)
    assert (
        game.players[nickname].settlements[entities.Coordinate(q=0, r=0, d=2)]
        is entities.SettlementType.TERRACE
    )


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [(0, 0, 0)],
            [
                (0, 0, 0),
                (0, 0, 1),
                (0, 0, 5),
                (1, -1, 3),
                (1, -1, 4),
                (1, -1, 5),
                (0, -1, 1),
                (0, -1, 2),
                (0, -1, 3),
            ],
        )
    ),
)
def test_terrace_cannot_be_added_to_restricted_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=valid[0], r=valid[1], direction=valid[2])
    _fund_path_purchase(game, nickname, count=3)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=5)
    buy_path(game, nickname, q=1, r=-1, direction=4)
    _fund_terrace_purchase(game, nickname)
    with pytest.raises(InvalidSettlementLocation):
        buy_terrace(game, nickname, q=invalid[0], r=invalid[1], direction=invalid[2])


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    buy_terrace(game, nickname, q=0, r=0, direction=2)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0
    assert game.players[nickname].resources[entities.ResourceCard.COTTON] == 0
    assert game.players[nickname].resources[entities.ResourceCard.MAIZE] == 0


def test_player_not_in_turn_cannot_buy_terrace(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    buy_path(game, nickname, q=0, r=0, direction=0)
    buy_path(game, nickname, q=0, r=0, direction=1)
    _fund_terrace_purchase(game, nickname)
    game._turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(PlayerNotInTurn):
        buy_terrace(game, nickname, q=0, r=0, direction=2)


def test_cannot_buy_terrace_if_not_enough_terraces_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    _fund_terrace_purchase(game, nickname, count=5)
    _fund_path_purchase(game, nickname, count=10)
    add_initial_terrace(game, nickname, q=0, r=-2, direction=0)
    buy_path(game, nickname, q=0, r=-2, direction=0)
    buy_path(game, nickname, q=1, r=-2, direction=5)
    buy_terrace(game, nickname, q=1, r=-2, direction=0)
    buy_path(game, nickname, q=1, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=5)
    buy_terrace(game, nickname, q=2, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=0)
    buy_path(game, nickname, q=2, r=-2, direction=1)
    buy_terrace(game, nickname, q=2, r=-2, direction=2)
    buy_path(game, nickname, q=2, r=-1, direction=0)
    buy_path(game, nickname, q=2, r=-1, direction=1)
    buy_terrace(game, nickname, q=2, r=-1, direction=2)
    buy_path(game, nickname, q=2, r=0, direction=0)
    buy_path(game, nickname, q=2, r=0, direction=1)
    with pytest.raises(InsufficientResources):
        buy_terrace(game, nickname, q=2, r=0, direction=2)


def _fund_path_purchase(
    game: entities.ActiveGame, nickname: str, *, count: int = 1
) -> None:
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: count,
            entities.ResourceCard.WOOD: count,
        }
    )


def _fund_terrace_purchase(
    game: entities.ActiveGame, nickname: str, *, count: int = 1
) -> None:
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.STONE: count,
            entities.ResourceCard.WOOD: count,
            entities.ResourceCard.COTTON: count,
            entities.ResourceCard.MAIZE: count,
        }
    )
