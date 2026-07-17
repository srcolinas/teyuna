from collections.abc import Container

from .. import entities


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
