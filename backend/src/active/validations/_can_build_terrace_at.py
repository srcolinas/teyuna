from collections.abc import Container

from .. import entities


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
