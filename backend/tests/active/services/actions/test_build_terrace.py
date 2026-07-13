import itertools

import pytest

from src.active import entities
from src.active.services import actions

from .... import utils

_TERRACE_COST = {
    entities.ResourceCard.STONE: 1,
    entities.ResourceCard.WOOD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}


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
def test_cannot_build_terrace_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(resources)
    with pytest.raises(actions.InsufficientResources):
        actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)


def test_terrace_needs_to_be_connected_to_a_path(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.resources.update(_TERRACE_COST)
    with pytest.raises(actions.InvalidSettlementLocation):
        actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)


def test_can_build_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    with utils.assert_not_raises(actions.InsufficientResources):
        actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)
    assert (
        player.settlements[entities.canonical_vertex(0, 0, 2)]
        is entities.SettlementType.TERRACE
    )


type Coordinate = tuple[int, int, int]


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [((0, 0, 0), (0, 0, 0), (0, 0, 5), (1, -1, 4))],
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
    valid: tuple[Coordinate, ...],
    invalid: Coordinate,
    game: entities.ActiveGame,
) -> None:
    terrace, path_coords = valid[0], valid[1:]
    player = game.players[game.active_player]
    player.settlements[
        entities.canonical_vertex(terrace[0], terrace[1], terrace[2])
    ] = entities.SettlementType.TERRACE
    for path in path_coords:
        player.paths.add(entities.canonical_edge(*path))
    game.restricted_verticies.add(entities.canonical_vertex(*invalid))
    player.resources.update(_TERRACE_COST)
    with pytest.raises(actions.InvalidSettlementLocation):
        actions.build_terrace(
            game,
            game.active_player,
            q=invalid[0],
            r=invalid[1],
            direction=invalid[2],
        )


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)
    assert player.resources[entities.ResourceCard.STONE] == 0
    assert player.resources[entities.ResourceCard.WOOD] == 0
    assert player.resources[entities.ResourceCard.COTTON] == 0
    assert player.resources[entities.ResourceCard.MAIZE] == 0


def test_cannot_build_terrace_if_not_enough_terraces_available(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    for i in range(entities.MAX_TERRACES):
        player.settlements[entities.Coordinate(q=0, r=0, d=i)] = (
            entities.SettlementType.TERRACE
        )
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    with pytest.raises(actions.InsufficientResources):
        actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)


def test_build_terrace_limits_free_verticies(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    original_free_verticies = game.free_verticies.copy()
    actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)
    assert game.free_verticies == original_free_verticies - {
        entities.canonical_vertex(0, 0, 2)
    }


def test_build_terrace_restricts_verticies_around_it(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.paths.add(entities.canonical_edge(0, 0, 0))
    player.paths.add(entities.canonical_edge(0, 0, 1))
    player.resources.update(_TERRACE_COST)
    actions.build_terrace(game, game.active_player, q=0, r=0, direction=2)
    assert game.restricted_verticies == {
        entities.canonical_vertex(1, 0, 3),
        entities.canonical_vertex(0, 0, 1),
        entities.canonical_vertex(0, 0, 3),
    }
