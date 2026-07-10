import pytest

from src.active import entities, services

from ... import utils


def test_cannot_add_path_if_player_is_not_in_turn(game: entities.ActiveGame) -> None:
    services.add_initial_terrace(game, game.turn_order[0], q=0, r=0, direction=0)
    game.turn_order = (game.turn_order[1], game.turn_order[0], game.turn_order[2])
    with pytest.raises(services.PlayerNotInTurn):
        services.add_initial_path(game, game.turn_order[1], q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "phase", [entities.GamePhase.MAIN, entities.GamePhase.FINISHED]
)
def test_cannot_add_path_if_not_in_initial_phase(
    phase: entities.GamePhase, game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    game.phase = phase
    with pytest.raises(services.InvalidGamePhase):
        services.add_initial_path(game, nickname, q=0, r=0, direction=0)


def test_path_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    with utils.assert_not_raises(Exception):
        services.add_initial_path(game, nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    services.add_initial_path(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].paths == {entities.Coordinate(q=0, r=0, d=0)}


def test_added_path_limits_free_edges(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    original_free_edges = game.free_edges.copy()
    services.add_initial_path(game, nickname, q=0, r=0, direction=0)
    assert game.free_edges == original_free_edges - {entities.Coordinate(q=0, r=0, d=0)}


def test_path_should_be_added_next_to_terrace(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    with pytest.raises(services.InvalidPathLocation):
        services.add_initial_path(game, nickname, q=0, r=0, direction=1)
