import pytest

from src.active import entities
from src.active.services import actions

from .... import utils


def test_path_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.active_player
    game.players[nickname].settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    with utils.assert_not_raises(Exception):
        actions.add_free_path(game, nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.active_player
    game.players[nickname].settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    actions.add_free_path(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].paths == {entities.canonical_edge(0, 0, 0)}


def test_added_path_limits_free_edges(game: entities.ActiveGame) -> None:
    nickname = game.active_player
    game.players[nickname].settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    original_free_edges = game.free_edges.copy()
    actions.add_free_path(game, nickname, q=0, r=0, direction=0)
    assert game.free_edges == original_free_edges - {entities.canonical_edge(0, 0, 0)}


def test_path_should_be_added_next_to_terrace(game: entities.ActiveGame) -> None:
    nickname = game.active_player
    game.players[nickname].settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    with pytest.raises(actions.InvalidPathLocation):
        actions.add_free_path(game, nickname, q=0, r=0, direction=1)
