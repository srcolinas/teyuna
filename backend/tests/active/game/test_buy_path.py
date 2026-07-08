import itertools

import pytest

from src.active import entities

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
    _fund_path_purchase(game, nickname)
    with utils.assert_not_raises(entities.InsufficientResources):
        game.buy_path(nickname, q=0, r=0, direction=0)


def test_path_can_be_bought_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname)
    with utils.assert_not_raises(Exception):
        game.buy_path(nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname)
    game.buy_path(nickname, q=0, r=0, direction=0)
    assert game.players[nickname].paths == {entities.Coordinate(q=0, r=0, d=0)}


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname)
    game.buy_path(nickname, q=0, r=0, direction=0)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0


def test_player_not_in_turn_cannot_buy_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname)
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(entities.PlayerNotInTurn):
        game.buy_path(nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [(0, 0, 0)],
            [
                (0, 0, 0),
                (1, -1, 3),
            ],
        )
    ),
)
def test_path_cannot_be_bought_at_occupied_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    q, r, d = valid
    game.add_initial_terrace(nickname, q=q, r=r, direction=d)
    _fund_path_purchase(game, nickname, count=2)
    game.buy_path(nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidPathLocation):
        q, r, d = invalid
        game.buy_path(nickname, q=q, r=r, direction=d)


def test_path_can_be_bought_next_to_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    _fund_path_purchase(game, nickname, count=2)
    game.buy_path(nickname, q=0, r=0, direction=0)
    with utils.assert_not_raises(Exception):
        game.buy_path(nickname, q=0, r=0, direction=1)


def test_path_cannot_be_bought_without_path_or_terrace_next_to_it(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    _fund_path_purchase(game, nickname)
    with pytest.raises(entities.InvalidPathLocation):
        game.buy_path(nickname, q=0, r=0, direction=0)


def test_path_cannot_be_bought_if_blocked_by_another_players_terrace(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=2)
    _fund_path_purchase(game, nickname, count=3)
    game.buy_path(nickname, q=0, r=0, direction=1)
    game.buy_path(nickname, q=0, r=0, direction=0)
    with pytest.raises(entities.InvalidPathLocation):
        game.buy_path(nickname, q=0, r=0, direction=5)


def test_cannot_buy_path_if_not_enough_paths_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=-2, direction=0)
    _fund_path_purchase(game, nickname, count=15)
    game.buy_path(nickname, q=0, r=-2, direction=0)
    game.buy_path(nickname, q=1, r=-2, direction=5)
    game.buy_path(nickname, q=1, r=-2, direction=0)
    game.buy_path(nickname, q=2, r=-2, direction=5)
    game.buy_path(nickname, q=2, r=-2, direction=0)
    game.buy_path(nickname, q=2, r=-2, direction=1)
    game.buy_path(nickname, q=2, r=-1, direction=0)
    game.buy_path(nickname, q=2, r=-1, direction=1)
    game.buy_path(nickname, q=2, r=0, direction=0)
    game.buy_path(nickname, q=2, r=0, direction=1)
    game.buy_path(nickname, q=2, r=0, direction=2)
    game.buy_path(nickname, q=1, r=1, direction=1)
    game.buy_path(nickname, q=1, r=1, direction=2)
    game.buy_path(nickname, q=0, r=2, direction=1)
    game.buy_path(nickname, q=0, r=2, direction=2)
    with pytest.raises(entities.InsufficientResources):
        game.buy_path(nickname, q=2, r=0, direction=2)
