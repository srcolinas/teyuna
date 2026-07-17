from collections.abc import Container

from .. import entities


def can_add_free_path_at(
    *,
    target: entities.Coordinate,
    neighbor_terrace: entities.Coordinate,
    free_edges: Container[entities.Coordinate],
    existing_settlements: Container[entities.Coordinate],
) -> bool:
    """Coordinates are expected in canonical form."""
    if target not in free_edges:
        return False
    if neighbor_terrace not in existing_settlements:
        return False
    return any(v == neighbor_terrace for v in entities.vertices_of_edge(target))
