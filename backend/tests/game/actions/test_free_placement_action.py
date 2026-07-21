from src.game import actions, entities


def test_free_placement_action_canonicalizes_coordinates() -> None:
    terrace_alias = next(iter(entities.vertex_aliases(0, 0, 0)))
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    path_alias = entities.edge_alias(path.q, path.r, path.d)

    action = actions.FreePlacementAction(
        by="player",
        terrace=terrace_alias,
        path=path_alias,
    )

    assert action.terrace == entities.canonical_vertex(0, 0, 0)
    assert action.path == entities.canonical_edge(path.q, path.r, path.d)
