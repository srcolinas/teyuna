import itertools

import pytest

from src.active import entities

from ... import utils


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    with utils.assert_not_raises(Exception):
        game.add_terrace(nickname, q=0, r=0, direction=0)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.add_terrace(nickname, q=0, r=0, direction=0)
    assert (
        game.players[nickname].settlements[
            entities.VertexCoordinate(entities.HexCoordinate(0, 0), 0)
        ]
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
    q, r, d = valid
    game.add_terrace(nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(entities.InvalidSettlementLocation):
        q, r, d = invalid
        game.add_terrace(nickname, q=q, r=r, direction=d)


def test_terrace_cannot_be_added_by_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[1]
    with pytest.raises(entities.PlayerNotInTurn):
        game.add_terrace(nickname, q=0, r=0, direction=0)
