import itertools

import pytest

from src.active import entities
from src.active.services import actions

from .... import utils


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    with utils.assert_not_raises(Exception):
        actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)
    settlements = game.players[nickname].settlements
    coord = entities.canonical_vertex(0, 0, 0)
    assert coord in settlements, settlements
    assert settlements[coord] is entities.SettlementType.TERRACE


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
    actions.add_free_terrace(game, nickname, q=q, r=r, direction=d)
    with pytest.raises(actions.InvalidSettlementLocation):
        q, r, d = invalid
        actions.add_free_terrace(game, nickname, q=q, r=r, direction=d)


def test_new_terrace_limits_free_verticies(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    original_free_verticies = game.free_verticies.copy()
    actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)
    assert game.free_verticies == original_free_verticies - {
        entities.canonical_vertex(0, 0, 0)
    }


def test_new_terrace_restricts_verticies_around_it(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)
    assert game.restricted_verticies == {
        entities.canonical_vertex(0, -1, 1),
        entities.canonical_vertex(-1, 0, 1),
        entities.canonical_vertex(0, 0, 1),
    }
