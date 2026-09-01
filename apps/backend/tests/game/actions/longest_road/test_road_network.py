from collections.abc import Set

import pytest

from src.game.actions.handlers import _longest_road
import teyuna_core

from . import helpers


def test_finds_all_pieces_in_network(
    network: Set[teyuna_core.Coordinate],
    alternative_network: Set[teyuna_core.Coordinate],
) -> None:
    for seed in network:
        result = _longest_road.road_network(
            seed,
            player_paths=set().union(network, alternative_network),
            traversable_vertices=helpers.AllVertices(),
        )
        assert result == network


@pytest.fixture(
    params=[
        "linear_chain_of_roads",
        "branches_without_loops",
        "single_closed_loop",
        "single_loop_with_single_branch",
        "single_loop_with_two_branches",
        "two_loops_sharing_edge",
        "two_loops_sharing_edge_with_a_branch",
        "two_loops_connected_through_edge",
    ]
)
def network(request: pytest.FixtureRequest) -> Set[teyuna_core.Coordinate]:
    return request.getfixturevalue(request.param)
