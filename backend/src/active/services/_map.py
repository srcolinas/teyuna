from typing import Final

from src.active import entities


def canonical_vertex(q: int, r: int, d: int) -> entities.Coordinate:
    aliases = vertex_aliases(q, r, d)
    aliases.add(entities.Coordinate(q=q, r=r, d=d))
    return min(aliases)


def vertex_aliases(q: int, r: int, d: int) -> set[entities.Coordinate]:
    dq, dr = delta_to_neighbor(d)
    dq5, dr5 = delta_to_neighbor((d + 5) % 6)
    return {
        entities.Coordinate(q=q + dq, r=r + dr, d=(d + 4) % 6),
        entities.Coordinate(q=q + dq5, r=r + dr5, d=(d + 2) % 6),
    }


def canonical_edge(q: int, r: int, d: int) -> entities.Coordinate:
    alias = edge_alias(q, r, d)
    return min(alias, entities.Coordinate(q=q, r=r, d=d))


def edge_alias(q: int, r: int, d: int) -> entities.Coordinate:
    dq, dr = delta_to_neighbor(d)
    return entities.Coordinate(q=q + dq, r=r + dr, d=(d + 3) % 6)


def delta_to_neighbor(d: int) -> tuple[int, int]:
    dq, dr = _NEIGHBOR[d]
    return dq, dr


_NEIGHBOR: Final[list[tuple[int, int]]] = [
    (1, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
]

HARBOUR_LOCATIONS: Final[dict[entities.Coordinate, entities.ResourceCard | None]] = {
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
