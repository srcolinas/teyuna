import dataclasses
from collections.abc import Set

import pytest

from src.game.actions.handlers import _longest_road
import teyuna_core

from . import helpers


@dataclasses.dataclass
class Case:
    network: Set[teyuna_core.Coordinate]
    seed: teyuna_core.Coordinate
    expected: int


def test_longest_road_from_seed(
    case: Case,
) -> None:
    result = _longest_road.longest_road_from_seed(
        case.seed,
        network=case.network,
        traversable_vertices=helpers.AllVertices(),
    )
    assert result == case.expected


@dataclasses.dataclass
class Params:
    network_fixture: str
    seed: teyuna_core.Coordinate
    expected: int


@pytest.fixture(
    params=[
        pytest.param(
            Params(
                network_fixture="linear_chain_of_roads",
                seed=teyuna_core.canonical_edge(0, 0, 0),
                expected=8,
            ),
            id="linear_chain_of_roads_tail",
        ),
        pytest.param(
            Params(
                network_fixture="linear_chain_of_roads",
                seed=teyuna_core.canonical_edge(0, 0, 2),
                expected=5,
            ),
            id="linear_chain_of_roads_middle",
        ),
        pytest.param(
            Params(
                network_fixture="branches_without_loops",
                seed=teyuna_core.canonical_edge(0, -1, 0),
                expected=9,
            ),
            id="branches_without_loops_longest_tail",
        ),
        pytest.param(
            Params(
                network_fixture="branches_without_loops",
                seed=teyuna_core.canonical_edge(1, -1, 2),
                expected=7,
            ),
            id="branches_without_loops_smallest_tail",
        ),
        pytest.param(
            Params(
                network_fixture="branches_without_loops",
                seed=teyuna_core.canonical_edge(0, 0, 1),
                expected=6,
            ),
            id="branches_without_loops_middle",
        ),
        pytest.param(
            Params(
                network_fixture="single_closed_loop",
                seed=teyuna_core.canonical_edge(0, 0, 0),
                expected=6,
            ),
            id="single_closed_loop",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, 0, 1),
                expected=7,
            ),
            id="single_loop_with_single_branch_far_right_from_branch",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, 0, 4),
                expected=7,
            ),
            id="single_loop_with_single_branch_far_left_from_branch",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, 0, 0),
                expected=8,
            ),
            id="single_loop_with_single_branch_right_to_branch",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, 0, 5),
                expected=8,
            ),
            id="single_loop_with_single_branch_left_to_branch",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, -1, 1),
                expected=7,
            ),
            id="single_loop_with_single_branch_next_to_loop",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                seed=teyuna_core.canonical_edge(0, -1, 0),
                expected=8,
            ),
            id="single_loop_with_single_branch_furthest_from_loop",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_two_branches",
                seed=teyuna_core.canonical_edge(0, 0, 1),
                expected=7,
            ),
            id="single_loop_with_two_branches_far_right_from_branches",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_two_branches",
                seed=teyuna_core.canonical_edge(0, -1, 3),
                expected=8,
            ),
            id="single_loop_with_two_branches_from_smallest_branch",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_sharing_edge",
                seed=teyuna_core.canonical_edge(0, 0, 5),
                expected=11,
            ),
            id="two_loops_sharing_edge_from_next_vertices_of_shared_edge",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_sharing_edge",
                seed=teyuna_core.canonical_edge(0, 0, 1),
                expected=10,
            ),
            id="two_loops_sharing_edge_from_far_vertices_of_shared_edge",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_sharing_edge_with_a_branch",
                seed=teyuna_core.canonical_edge(1, -1, 0),
                expected=12,
            ),
            id="two_loops_sharing_edge_with_a_branch_from_branch_tail",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_connected_through_edge",
                seed=teyuna_core.canonical_edge(-1, 1, 5),
                expected=7,
            ),
            id="two_loops_connected_through_edge_from_bridge",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_connected_through_edge",
                seed=teyuna_core.canonical_edge(0, 0, 3),
                expected=13,
            ),
            id="two_loops_connected_through_edge_from_loop_next_to_bridge",
        ),
    ]
)
def case(request: pytest.FixtureRequest) -> Case:
    return Case(
        network=request.getfixturevalue(request.param.network_fixture),
        seed=request.param.seed,
        expected=request.param.expected,
    )
