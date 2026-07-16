from collections.abc import Set

from .. import entities


def can_add_free_terrace_at(
    *,
    free_verticies: Set[entities.Coordinate],
    restricted_verticies: Set[entities.Coordinate],
    target: entities.Coordinate,
) -> tuple[bool, set[entities.Coordinate]]:
    """Returns whether the terrace can be added and the vertices that will be restricted"""
    target = entities.canonical_vertex(target.q, target.r, target.d)
    if target not in free_verticies or target in restricted_verticies:
        return False, set()

    dq5, dr5 = entities.delta_to_neighbor((target.d + 5) % 6)
    blocked_vertices = {
        entities.canonical_vertex(vq, vr, vd)
        for vq, vr, vd in [
            (target.q, target.r, (target.d + 1) % 6),
            (target.q, target.r, (target.d + 5) % 6),
            (target.q + dq5, target.r + dr5, (target.d + 1) % 6),
        ]
    }
    return True, blocked_vertices
