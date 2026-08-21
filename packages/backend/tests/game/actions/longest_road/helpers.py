from typing import Container, Iterable

from src.game import entities
import teyuna_core


def place_buildings(
    game: entities.Game,
    nickname: str,
    *,
    edges: list[tuple[int, int, int]],
    vertices: list[tuple[int, int, int]],
) -> teyuna_core.Coordinate:
    """Place a seed terrace then paths so board sets stay consistent."""
    for q, r, d in vertices:
        game.use_vertex(
            nickname,
            teyuna_core.canonical_vertex(q, r, d),
            teyuna_core.SettlementType.TERRACE,
        )

    last = teyuna_core.canonical_edge(*edges[0])
    game.use_edge(nickname, last)
    for q, r, d in edges[1:]:
        last = teyuna_core.canonical_edge(q, r, d)
        game.use_edge(nickname, last)
    return last


def vertices_of_hexagons(
    hexagons: Iterable[tuple[int, int]],
) -> set[teyuna_core.Coordinate]:
    return {
        teyuna_core.canonical_vertex(q, r, d) for q, r in hexagons for d in range(6)
    }


class AllVertices(Container):
    def __contains__(self, item: object) -> bool:
        return True
