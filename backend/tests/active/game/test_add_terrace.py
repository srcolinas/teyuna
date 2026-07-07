import itertools

import pytest

from src.active import entities

from ... import utils


def test_terrace_needs_to_be_connected_to_a_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidSettlementLocation):
        game.add_terrace(nickname, q=0, r=0, direction=0)


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    with utils.assert_not_raises(Exception):
        game.add_terrace(nickname, q=0, r=0, direction=2)


def test_terrace_cannot_be_added_by_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(entities.PlayerNotInTurn):
        game.add_terrace(nickname, q=0, r=0, direction=2)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_initial_terrace(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=1)
    game.add_terrace(nickname, q=0, r=0, direction=2)
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
    game.add_initial_terrace(nickname, q=valid[0], r=valid[1], direction=valid[2])
    game.add_path(nickname, q=0, r=0, direction=0)
    game.add_path(nickname, q=0, r=0, direction=5)
    game.add_path(nickname, q=1, r=-1, direction=4)
    with pytest.raises(entities.InvalidSettlementLocation):
        game.add_terrace(nickname, q=invalid[0], r=invalid[1], direction=invalid[2])
