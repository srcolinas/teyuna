from collections.abc import Container

from ... import entities


def can_add_free_path_at(
    *,
    target: entities.Coordinate,
    free_edges: Container[entities.Coordinate],
    existing_settlements: Container[entities.Coordinate],
    existing_paths: Container[entities.Coordinate],
    free_vertices: Container[entities.Coordinate],
) -> bool:
    """Coordinates are expected in canonical form."""
    if target not in free_edges:
        return False

    for v in entities.vertices_of_edge(target):
        if v in existing_settlements:
            return True
        if v in free_vertices:
            for e in entities.edges_adjacent_to_vertex(v.q, v.r, v.d):
                if e != target and e in existing_paths:
                    return True
    return False


def can_add_free_terrace_at(
    *,
    free_verticies: Container[entities.Coordinate],
    restricted_verticies: Container[entities.Coordinate],
    target: entities.Coordinate,
) -> bool:
    """Returns whether the terrace can be added.

    Coordinates are expected in canonical form.
    """
    return target in free_verticies and target not in restricted_verticies


def can_build_terrace_at(
    *,
    free_verticies: Container[entities.Coordinate],
    restricted_verticies: Container[entities.Coordinate],
    existing_paths: Container[entities.Coordinate],
    target: entities.Coordinate,
) -> bool:
    """Returns whether a paid terrace can be built at target.

    Coordinates are expected in canonical form. The vertex must be free and
    unrestricted, and at least one adjacent edge must be owned.
    """
    if target not in free_verticies or target in restricted_verticies:
        return False
    return any(
        edge in existing_paths
        for edge in entities.edges_adjacent_to_vertex(target.q, target.r, target.d)
    )
