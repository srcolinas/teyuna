import itertools

import pytest

from src.active import InvalidGamePhase, InvalidSettlementLocation, PlayerNotInTurn
from src.active import entities
from src.active.services import add_initial_terrace

from ... import utils


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    with utils.assert_not_raises(Exception):
        add_initial_terrace(game, nickname, q=0, r=0, direction=0)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    settlements = game.players[nickname].settlements
    # NOTE: this is the canonical coordinate for the terrace
    coord = entities.Coordinate(q=0, r=-1, d=2)
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
    add_initial_terrace(game, nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(InvalidSettlementLocation):
        q, r, d = invalid
        add_initial_terrace(game, nickname, q=q, r=r, direction=d)


def test_terrace_cannot_be_added_by_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[1]
    with pytest.raises(PlayerNotInTurn):
        add_initial_terrace(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "phase",
    [
        entities.GamePhase.MAIN,
        entities.GamePhase.FINISHED,
    ],
)
def test_cannot_add_terrace_if_game_is_not_in_initial_phase(
    phase: entities.GamePhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game._phase = phase
    with pytest.raises(InvalidGamePhase):
        add_initial_terrace(game, nickname, q=0, r=0, direction=0)
