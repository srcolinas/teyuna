from collections.abc import Set

import pytest

import teyuna_core


@pytest.fixture
def linear_chain_of_roads() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(1, 0, 3),
        teyuna_core.canonical_edge(1, 0, 2),
        teyuna_core.canonical_edge(1, 0, 1),
    }


@pytest.fixture
def branches_without_loops() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, -1, 0),
        teyuna_core.canonical_edge(0, -1, 1),
        teyuna_core.canonical_edge(-1, 0, 0),
        teyuna_core.canonical_edge(-1, 0, 5),
        teyuna_core.canonical_edge(1, -1, 2),
    }


@pytest.fixture
def single_closed_loop() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
    }


@pytest.fixture
def single_loop_with_single_branch() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(0, -1, 0),
        teyuna_core.canonical_edge(0, -1, 1),
    }


@pytest.fixture
def single_loop_with_two_branches() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(0, -1, 0),
        teyuna_core.canonical_edge(0, -1, 1),
        teyuna_core.canonical_edge(0, -1, 3),
    }


@pytest.fixture
def two_loops_sharing_edge() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(0, -1, 0),
        teyuna_core.canonical_edge(0, -1, 1),
        teyuna_core.canonical_edge(0, -1, 3),
        teyuna_core.canonical_edge(0, -1, 4),
        teyuna_core.canonical_edge(0, -1, 5),
    }


@pytest.fixture
def two_loops_sharing_edge_with_a_branch() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(0, -1, 0),
        teyuna_core.canonical_edge(0, -1, 1),
        teyuna_core.canonical_edge(0, -1, 3),
        teyuna_core.canonical_edge(0, -1, 4),
        teyuna_core.canonical_edge(0, -1, 5),
        teyuna_core.canonical_edge(1, -1, 5),
        teyuna_core.canonical_edge(1, -1, 0),
    }


@pytest.fixture
def two_loops_connected_through_edge() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(0, 0, 0),
        teyuna_core.canonical_edge(0, 0, 1),
        teyuna_core.canonical_edge(0, 0, 2),
        teyuna_core.canonical_edge(0, 0, 3),
        teyuna_core.canonical_edge(0, 0, 4),
        teyuna_core.canonical_edge(0, 0, 5),
        teyuna_core.canonical_edge(-2, 1, 0),
        teyuna_core.canonical_edge(-2, 1, 1),
        teyuna_core.canonical_edge(-2, 1, 2),
        teyuna_core.canonical_edge(-2, 1, 3),
        teyuna_core.canonical_edge(-2, 1, 4),
        teyuna_core.canonical_edge(-2, 1, 5),
        teyuna_core.canonical_edge(-1, 1, 5),
    }


@pytest.fixture
def alternative_network() -> Set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_edge(2, -2, 0),
        teyuna_core.canonical_edge(2, -2, 1),
    }
