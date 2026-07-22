"""Hex board geometry helpers for placement decisions.

Duplicated from the backend domain model so this package does not import it.
Public Game DTOs do not expose free/restricted sets — those are derived here.
"""

from __future__ import annotations

import itertools
from typing import Final, NamedTuple

from . import entities

INVALID_HEX_COORDINATES: Final[set[tuple[int, int]]] = {
    (-2, -2),
    (-2, -1),
    (-1, -2),
    (1, 2),
    (2, 1),
    (2, 2),
}

_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]


class Coordinate(NamedTuple):
    q: int
    r: int
    d: int


def delta_to_neighbor(d: int) -> tuple[int, int]:
    return _NEIGHBOR[d]


def _is_valid_hex(q: int, r: int) -> bool:
    return -2 <= q <= 2 and -2 <= r <= 2 and (q, r) not in INVALID_HEX_COORDINATES


def _canonical_among(candidates: set[Coordinate]) -> Coordinate:
    valid = {c for c in candidates if _is_valid_hex(c.q, c.r)}
    if not valid:
        raise ValueError("no valid board hex among coordinate aliases")
    return min(valid)


def vertex_aliases(q: int, r: int, d: int) -> set[Coordinate]:
    dq, dr = delta_to_neighbor(d)
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    return {
        Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_vertex(q: int, r: int, d: int) -> Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(Coordinate(q=q, r=r, d=d))
    return _canonical_among(aliases)


def edge_alias(q: int, r: int, d: int) -> Coordinate:
    dq, dr = delta_to_neighbor(d)
    return Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


def canonical_edge(q: int, r: int, d: int) -> Coordinate:
    return _canonical_among({edge_alias(q, r, d), Coordinate(q=q, r=r, d=d)})


def vertices_of_edge(edge: Coordinate) -> tuple[Coordinate, Coordinate]:
    q, r, d = edge
    return (
        canonical_vertex(q, r, d),
        canonical_vertex(q, r, (d + 1) % 6),
    )


def edges_adjacent_to_vertex(q: int, r: int, d: int) -> set[Coordinate]:
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    adjacent: set[Coordinate] = set()
    for edge_q, edge_r, edge_d in (
        (q, r, (d + 5) % 6),
        (q, r, d),
        (q + dq5, r + dr5, (d + 1) % 6),
    ):
        try:
            adjacent.add(canonical_edge(edge_q, edge_r, edge_d))
        except ValueError:
            continue
    return adjacent


def restricted_vertices_for(target: Coordinate) -> set[Coordinate]:
    dq5, dr5 = delta_to_neighbor((target.d + 5) % 6)
    blocked: set[Coordinate] = set()
    for vq, vr, vd in (
        (target.q, target.r, (target.d + 1) % 6),
        (target.q, target.r, (target.d + 5) % 6),
        (target.q + dq5, target.r + dr5, (target.d + 1) % 6),
    ):
        try:
            blocked.add(canonical_vertex(vq, vr, vd))
        except ValueError:
            continue
    return blocked


def from_vertex(location: entities.VertexCoordinate) -> Coordinate:
    return canonical_vertex(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def from_edge(location: entities.EdgeCoordinate) -> Coordinate:
    return canonical_edge(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def to_vertex(coord: Coordinate) -> entities.VertexCoordinate:
    return entities.VertexCoordinate(
        hex_coord=entities.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def to_edge(coord: Coordinate) -> entities.EdgeCoordinate:
    return entities.EdgeCoordinate(
        hex_coord=entities.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def all_board_vertices() -> set[Coordinate]:
    vertices: set[Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in INVALID_HEX_COORDINATES:
            vertices.add(canonical_vertex(q, r, d))
    return vertices


def all_board_edges() -> set[Coordinate]:
    edges: set[Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in INVALID_HEX_COORDINATES:
            edges.add(canonical_edge(q, r, d))
    return edges


def placement_sets(
    game: entities.Game,
) -> tuple[set[Coordinate], set[Coordinate]]:
    """Return (buildable_vertices, free_edges).

    buildable_vertices = free vertices minus restricted (adjacent to settlements).
    free_edges = board edges without a path.
    """
    occupied_vertices = {from_vertex(s.location) for s in game.settlements}
    occupied_edges = {from_edge(p.location) for p in game.paths}

    restricted: set[Coordinate] = set()
    for settlement in game.settlements:
        restricted.update(restricted_vertices_for(from_vertex(settlement.location)))

    free_vertices = all_board_vertices() - occupied_vertices
    buildable = free_vertices - restricted
    free_edges = all_board_edges() - occupied_edges
    return buildable, free_edges
