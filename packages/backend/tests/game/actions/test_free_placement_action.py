import teyuna_core


def test_free_placement_action_canonicalizes_coordinates() -> None:
    terrace_alias = next(iter(teyuna_core.vertex_aliases(0, 0, 0)))
    path = next(iter(teyuna_core.edges_adjacent_to_vertex(0, 0, 0)))
    path_alias = teyuna_core.edge_alias(path.q, path.r, path.d)

    action = teyuna_core.FreePlacementAction(
        terrace=terrace_alias,
        path=path_alias,
    )

    assert action.terrace == teyuna_core.canonical_vertex(0, 0, 0)
    assert action.path == teyuna_core.canonical_edge(path.q, path.r, path.d)


def test_free_placement_action_allows_omitted_coordinates() -> None:
    action = teyuna_core.FreePlacementAction()

    assert action.terrace is None
    assert action.path is None
