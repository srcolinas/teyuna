from collections.abc import Collection, Container, Mapping

from ... import player
from ... import entities


def _sorted_coords(
    coords: Collection[entities.Coordinate],
) -> list[entities.Coordinate]:
    return sorted(coords)


def format_invalid_settlement_location(
    *,
    target: entities.Coordinate,
    player: player.Nickname,
    free_vertices: Collection[entities.Coordinate],
    restricted_vertices: Collection[entities.Coordinate],
    existing_paths: Collection[entities.Coordinate] = (),
    existing_settlements: Mapping[entities.Coordinate, entities.SettlementType]
    | None = None,
    reason: str | None = None,
) -> str:
    parts = [
        f"Player {player} cannot place settlement at {target}",
    ]
    if reason is not None:
        parts.append(reason)
    parts.append(f"free_vertices={_sorted_coords(free_vertices)}")
    parts.append(f"restricted_vertices={_sorted_coords(restricted_vertices)}")
    if existing_paths:
        parts.append(f"existing_paths={_sorted_coords(existing_paths)}")
    if existing_settlements is not None:
        settlements = {
            coord: settlement_type
            for coord, settlement_type in sorted(existing_settlements.items())
        }
        parts.append(f"existing_settlements={settlements}")
    return "; ".join(parts)


def format_invalid_path_location(
    *,
    target: entities.Coordinate,
    player: player.Nickname,
    existing_settlements: Collection[entities.Coordinate],
    existing_paths: Collection[entities.Coordinate],
    free_edges: Collection[entities.Coordinate],
) -> str:
    return (
        f"Player {player} cannot place path at {target}; "
        f"existing_settlements={_sorted_coords(existing_settlements)}; "
        f"existing_paths={_sorted_coords(existing_paths)}; "
        f"free_edges={_sorted_coords(free_edges)}"
    )


def format_invalid_conquistator_location(
    *,
    target: entities.HexLocation,
    player: player.Nickname,
    current_location: entities.HexLocation,
) -> str:
    return (
        f"Player {player} cannot move conquistator to {target}; "
        f"current_location={current_location}"
    )


def can_add_free_path_at(
    *,
    target: entities.Coordinate,
    free_edges: Container[entities.Coordinate],
    existing_settlements: Container[entities.Coordinate],
    existing_paths: Container[entities.Coordinate],
    free_vertices: Container[entities.Coordinate],
    new_settlement: entities.Coordinate | None = None,
) -> bool:
    """Coordinates are expected in canonical form.

    ``new_settlement`` is treated as owned for adjacency (e.g. same-action terrace).
    """
    if target not in free_edges:
        return False

    for v in entities.vertices_of_edge(target):
        if v in existing_settlements or v == new_settlement:
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
