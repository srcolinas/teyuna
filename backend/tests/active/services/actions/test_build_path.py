import itertools

import pytest

from src.active import entities
from src.active.services import actions

from .... import utils

_PATH_COST = {
    entities.ResourceCard.STONE: 1,
    entities.ResourceCard.WOOD: 1,
}


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
def test_cannot_build_path_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(resources)
    with pytest.raises(actions.InsufficientResources):
        actions.build_path(game, game.active_player, q=0, r=0, direction=1)


def test_can_build_path_with_sufficient_resources(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_PATH_COST)
    with utils.assert_not_raises(actions.InsufficientResources):
        actions.build_path(game, game.active_player, q=0, r=0, direction=0)


def test_path_can_be_bought_by_player_in_turn(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_PATH_COST)
    with utils.assert_not_raises(Exception):
        actions.build_path(game, game.active_player, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_PATH_COST)
    actions.build_path(game, game.active_player, q=0, r=0, direction=0)
    assert player.paths == {entities.canonical_edge(0, 0, 0)}


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_PATH_COST)
    actions.build_path(game, game.active_player, q=0, r=0, direction=0)
    assert player.resources[entities.ResourceCard.STONE] == 0
    assert player.resources[entities.ResourceCard.WOOD] == 0


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
    player = game.players[game.active_player]
    q, r, d = valid
    player.settlements[entities.canonical_vertex(q, r, d)] = (
        entities.SettlementType.TERRACE
    )
    occupied = entities.canonical_edge(q, r, d)
    player.paths.add(occupied)
    game.free_edges.remove(occupied)
    player.resources.update(_PATH_COST)
    with pytest.raises(actions.InvalidPathLocation):
        iq, ir, id_ = invalid
        actions.build_path(game, game.active_player, q=iq, r=ir, direction=id_)


def test_path_can_be_bought_next_to_path(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    existing = entities.canonical_edge(0, 0, 0)
    player.paths.add(existing)
    game.free_edges.remove(existing)
    player.resources.update(_PATH_COST)
    with utils.assert_not_raises(Exception):
        actions.build_path(game, game.active_player, q=0, r=0, direction=1)


def test_path_cannot_be_bought_without_path_or_terrace_next_to_it(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.resources.update(_PATH_COST)
    with pytest.raises(actions.InvalidPathLocation):
        actions.build_path(game, game.active_player, q=0, r=0, direction=0)


def test_path_cannot_be_bought_if_blocked_by_another_players_terrace(
    game: entities.ActiveGame,
) -> None:
    first = game.turn_order[0]
    second = game.turn_order[1]
    first_terrace = entities.canonical_vertex(0, 0, 0)
    second_terrace = entities.canonical_vertex(0, 0, 2)
    game.players[first].settlements[first_terrace] = entities.SettlementType.TERRACE
    game.players[second].settlements[second_terrace] = entities.SettlementType.TERRACE
    game.free_verticies.remove(first_terrace)
    game.free_verticies.remove(second_terrace)
    game.player_idx = 1
    player = game.players[second]
    for edge in (
        entities.canonical_edge(0, 0, 1),
        entities.canonical_edge(0, 0, 0),
    ):
        player.paths.add(edge)
        game.free_edges.remove(edge)
    player.resources.update(_PATH_COST)
    with pytest.raises(actions.InvalidPathLocation):
        actions.build_path(game, second, q=0, r=0, direction=5)


def test_cannot_build_path_if_not_enough_paths_available(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    for edge in list(game.free_edges)[: entities.MAX_PATHS]:
        player.paths.add(edge)
        game.free_edges.remove(edge)
    player.resources.update(_PATH_COST)
    remaining = next(iter(game.free_edges))
    with pytest.raises(actions.InsufficientResources):
        actions.build_path(
            game,
            game.active_player,
            q=remaining.q,
            r=remaining.r,
            direction=remaining.d,
        )


def test_build_path_limits_free_edges(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_PATH_COST)
    original_free_edges = game.free_edges.copy()
    actions.build_path(game, game.active_player, q=0, r=0, direction=0)
    assert game.free_edges == original_free_edges - {entities.canonical_edge(0, 0, 0)}
