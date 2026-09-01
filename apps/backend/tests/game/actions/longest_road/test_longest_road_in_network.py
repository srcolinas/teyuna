import dataclasses
from collections.abc import Set

import pytest

from src.game.actions.handlers import _longest_road
import teyuna_core

from . import helpers


@dataclasses.dataclass
class Case:
    network: Set[teyuna_core.Coordinate]
    expected: int


def test_longest_road_in_network(
    case: Case,
) -> None:
    for seed in case.network:
        result = _longest_road.longest_road_in_network(
            seed,
            player_paths=case.network,
            traversable_vertices=helpers.AllVertices(),
        )
        assert result == case.expected


@dataclasses.dataclass
class Params:
    network_fixture: str
    expected: int


@pytest.fixture(
    params=[
        pytest.param(
            Params(
                network_fixture="linear_chain_of_roads",
                expected=8,
            ),
            id="linear_chain_of_roads",
        ),
        pytest.param(
            Params(
                network_fixture="branches_without_loops",
                expected=9,
            ),
            id="branches_without_loops",
        ),
        pytest.param(
            Params(
                network_fixture="single_closed_loop",
                expected=6,
            ),
            id="single_closed_loop",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_single_branch",
                expected=8,
            ),
            id="single_loop_with_single_branch",
        ),
        pytest.param(
            Params(
                network_fixture="single_loop_with_two_branches",
                expected=8,
            ),
            id="single_loop_with_two_branches",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_sharing_edge",
                expected=11,
            ),
            id="two_loops_sharing_edge",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_sharing_edge_with_a_branch",
                expected=12,
            ),
            id="two_loops_sharing_edge_with_a_branch",
        ),
        pytest.param(
            Params(
                network_fixture="two_loops_connected_through_edge",
                expected=13,
            ),
            id="two_loops_connected_through_edge",
        ),
    ]
)
def case(request: pytest.FixtureRequest) -> Case:
    return Case(
        network=request.getfixturevalue(request.param.network_fixture),
        expected=request.param.expected,
    )
