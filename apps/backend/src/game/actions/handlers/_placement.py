from collections.abc import Container

import teyuna_core


def format_invalid_settlement_location(
    *,
    target: teyuna_core.Coordinate,
    player: str,
    reason: str | None = None,
) -> str:
    parts = [
        f"Player {player} cannot place settlement at {target}",
    ]
    if reason is not None:
        parts.append(reason)
    return "; ".join(parts)


def format_invalid_path_location(
    *,
    target: teyuna_core.Coordinate,
    player: str,
    reason: str | None = None,
) -> str:
    parts = [
        f"Player {player} cannot place path at {target}",
    ]
    if reason is not None:
        parts.append(reason)
    return "; ".join(parts)


def format_invalid_conquistator_location(
    *,
    target: teyuna_core.HexLocation,
    player: str,
    current_location: teyuna_core.HexLocation,
) -> str:
    return (
        f"Player {player} cannot move conquistator to {target}; "
        f"current_location={current_location}"
    )


PATH_EDGE_NOT_FREE = "The edge is occupied or is not a valid path location."
PATH_MUST_ADJOIN_NEW_TERRACE = "The path must adjoin the terrace being placed."
PATH_MUST_CONNECT_NETWORK = (
    "The path must adjoin one of your settlements or extend your path network."
)


def can_add_free_path_at(
    *,
    target: teyuna_core.Coordinate,
    free_edges: Container[teyuna_core.Coordinate],
    existing_settlements: Container[teyuna_core.Coordinate],
    existing_paths: Container[teyuna_core.Coordinate],
    free_vertices: Container[teyuna_core.Coordinate],
    new_settlement: teyuna_core.Coordinate | None = None,
) -> str | None:
    """Coordinates are expected in canonical form.

    Returns ``None`` if the path may be placed, otherwise a player-facing
    reason. When ``new_settlement`` is set (first/second free placement), the
    path must adjoin that terrace only. Otherwise the path may adjoin an owned
    settlement or extend an owned path network (paid builds / pathfinder).
    """
    if target not in free_edges:
        return PATH_EDGE_NOT_FREE

    if new_settlement is not None:
        if new_settlement in teyuna_core.vertices_of_edge(target):
            return None
        return PATH_MUST_ADJOIN_NEW_TERRACE

    for v in teyuna_core.vertices_of_edge(target):
        if v in existing_settlements:
            return None
        if v in free_vertices:
            for e in teyuna_core.edges_adjacent_to_vertex(v):
                if e != target and e in existing_paths:
                    return None
    return PATH_MUST_CONNECT_NETWORK


def can_add_free_terrace_at(
    *,
    free_verticies: Container[teyuna_core.Coordinate],
    restricted_verticies: Container[teyuna_core.Coordinate],
    target: teyuna_core.Coordinate,
) -> bool:
    """Returns whether the terrace can be added.

    Coordinates are expected in canonical form.
    """
    return target in free_verticies and target not in restricted_verticies


def can_build_terrace_at(
    *,
    free_verticies: Container[teyuna_core.Coordinate],
    restricted_verticies: Container[teyuna_core.Coordinate],
    existing_paths: Container[teyuna_core.Coordinate],
    target: teyuna_core.Coordinate,
) -> bool:
    """Returns whether a paid terrace can be built at target.

    Coordinates are expected in canonical form. The vertex must be free and
    unrestricted, and at least one adjacent edge must be owned.
    """
    if target not in free_verticies or target in restricted_verticies:
        return False
    return any(
        edge in existing_paths for edge in teyuna_core.edges_adjacent_to_vertex(target)
    )
