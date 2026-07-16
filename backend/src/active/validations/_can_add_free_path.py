from collections.abc import Set

from .. import entities


def can_add_free_path_at(
    *,
    target: entities.Coordinate,
    neighbor_terrace: entities.Coordinate,
    free_edges: Set[entities.Coordinate],
) -> bool:
    target = entities.canonical_edge(target.q, target.r, target.d)
    for v in entities.vertices_of_edge(target):
        if v == neighbor_terrace and v in free_edges:
            return True
    return False
