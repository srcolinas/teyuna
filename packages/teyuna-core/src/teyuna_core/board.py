import itertools
from typing import Annotated, Final, NamedTuple

import pydantic

from . import constants, entities


_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]


class Coordinate(pydantic.BaseModel):
    """Coordinate for a vertex (corner) or edge of a hex.

    A vertex or edge is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top vertex, going clockwise.
    """

    q: int
    r: int
    d: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Coordinate):
            return NotImplemented
        return (self.q, self.r, self.d) < (other.q, other.r, other.d)


class HexLocation(pydantic.BaseModel):
    """Coordinates of a hex, not including any vertex or edge.

    Uses the axial coordinate system (q, r).
    See: https://www.redblobgames.com/grids/hexagons/.
    """

    q: Annotated[
        int,
        pydantic.Field(
            description="0 along the top left to bottom right diagonal of the board, positives to the right",
        ),
    ]
    r: Annotated[
        int,
        pydantic.Field(
            description="0 along the horizontal axes of the board, positives to the bottom",
        ),
    ]

    model_config = pydantic.ConfigDict(frozen=True)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, HexLocation):
            return NotImplemented
        return (self.q, self.r) < (other.q, other.r)


def delta_to_neighbor(d: int) -> tuple[int, int]:
    dq, dr = _NEIGHBOR[d]
    return dq, dr


def _is_valid_hex(q: int, r: int) -> bool:
    return (
        -2 <= q <= 2
        and -2 <= r <= 2
        and (q, r) not in constants.INVALID_HEX_COORDINATES
    )


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


def vertices_of_edge(
    edge: Coordinate,
) -> tuple[Coordinate, Coordinate]:
    return (
        canonical_vertex(edge.q, edge.r, edge.d),
        canonical_vertex(edge.q, edge.r, (edge.d + 1) % 6),
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


def hex_locations_at_vertex(q: int, r: int, d: int) -> set[HexLocation]:
    """Return the valid board hexes that meet at the given vertex."""
    locs = {HexLocation(q=q, r=r)}
    for alias in vertex_aliases(q, r, d):
        locs.add(HexLocation(q=alias.q, r=alias.r))
    return {loc for loc in locs if _is_valid_hex(loc.q, loc.r)}


def all_board_vertices(
    invalid_hex_coordinates: set[tuple[int, int]] | None = None,
) -> set[Coordinate]:
    if invalid_hex_coordinates is None:
        invalid_hex_coordinates = constants.INVALID_HEX_COORDINATES
    vertices: set[Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in invalid_hex_coordinates:
            vertices.add(canonical_vertex(q, r, d))
    return vertices


def all_board_edges(
    invalid_hex_coordinates: set[tuple[int, int]] | None = None,
) -> set[Coordinate]:
    if invalid_hex_coordinates is None:
        invalid_hex_coordinates = constants.INVALID_HEX_COORDINATES
    edges: set[Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in invalid_hex_coordinates:
            edges.add(canonical_edge(q, r, d))
    return edges


HARBOUR_LOCATIONS: Final[dict[Coordinate, entities.ResourceCard | None]] = {
    canonical_vertex(-1, -1, 4): entities.ResourceCard.WOOD,
    canonical_vertex(-1, -1, 5): entities.ResourceCard.WOOD,
    canonical_vertex(0, -2, 0): None,
    canonical_vertex(0, -2, 5): None,
    canonical_vertex(1, -2, 0): entities.ResourceCard.MAIZE,
    canonical_vertex(1, -2, 1): entities.ResourceCard.MAIZE,
    canonical_vertex(2, -1, 0): entities.ResourceCard.STONE,
    canonical_vertex(2, -1, 1): entities.ResourceCard.STONE,
    canonical_vertex(2, 0, 1): None,
    canonical_vertex(2, 0, 2): None,
    canonical_vertex(1, 1, 2): entities.ResourceCard.COTTON,
    canonical_vertex(1, 1, 3): entities.ResourceCard.COTTON,
    canonical_vertex(-1, 2, 2): None,
    canonical_vertex(-1, 2, 3): None,
    canonical_vertex(-2, 2, 3): None,
    canonical_vertex(-2, 2, 4): None,
    canonical_vertex(-2, 1, 4): entities.ResourceCard.GOLD,
    canonical_vertex(-2, 1, 5): entities.ResourceCard.GOLD,
}


class HarbourPair(NamedTuple):
    """One harbour: a trade discount shared by two docking vertices."""

    resource: entities.ResourceCard | None
    vertices: tuple[Coordinate, Coordinate]


def default_harbour_pairs() -> tuple[HarbourPair, ...]:
    """Group ``HARBOUR_LOCATIONS`` into harbour pairs (insertion order)."""
    items = list(HARBOUR_LOCATIONS.items())
    pairs: list[HarbourPair] = []
    for i in range(0, len(items), 2):
        (loc_a, resource_a), (loc_b, resource_b) = items[i], items[i + 1]
        if resource_a != resource_b:
            raise ValueError("harbour location pairs must share a resource")
        pairs.append(HarbourPair(resource=resource_a, vertices=(loc_a, loc_b)))
    return tuple(pairs)


def harbour_locations_from_pairs(
    harbours: tuple[HarbourPair, ...],
) -> dict[Coordinate, entities.ResourceCard | None]:
    """Flatten harbour pairs into a vertex → resource lookup."""
    locations: dict[Coordinate, entities.ResourceCard | None] = {}
    for harbour in harbours:
        for vertex in harbour.vertices:
            locations[vertex] = harbour.resource
    return locations
