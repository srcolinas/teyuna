import itertools

import pytest

from src.active import entities

from ... import utils


def test_path_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    with utils.assert_not_raises(Exception):
        game.add_path(nickname, q=0, r=0, direction=0)


def test_path_cannot_be_added_by_player_not_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    nickname = game.turn_order[1]
    with pytest.raises(entities.PlayerNotInTurn):
        game.add_path(nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    assert game.players[nickname].paths == {entities.Coordinate(q=0, r=0, d=0)}


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
def test_path_cannot_be_added_to_occupied_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    q, r, d = valid
    game.add_terrace(nickname, q=q, r=r, direction=d)
    game.add_path(nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidPathLocation):
        q, r, d = invalid
        game.add_path(nickname, q=q, r=r, direction=d)


def test_path_can_be_added_next_to_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    with utils.assert_not_raises(Exception):
        game.add_path(nickname, q=0, r=0, direction=1)


def test_path_cannot_be_added_without_path_or_terrace_next_to_it(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidPathLocation):
        game.add_path(nickname, q=0, r=0, direction=0)


def test_path_cannot_be_added_if_blocked_by_another_players_terrace(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=2)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.add_path(nickname, q=0, r=0, direction=0)
    with pytest.raises(entities.InvalidPathLocation):
        game.add_path(nickname, q=0, r=0, direction=5)
