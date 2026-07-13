import collections
import itertools

import pytest

from src.active import entities


@pytest.fixture
def game() -> entities.ActiveGame:
    free_verticies, free_edges = _initial_buildable_locations()
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    return entities.ActiveGame(
        map=(mountains,),
        conquistator_location=mountains,
        turn_order=("srcolinas-1", "srcolinas-2", "srcolinas-3"),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in ("srcolinas-1", "srcolinas-2", "srcolinas-3")
        },
        free_verticies=free_verticies,
        free_edges=free_edges,
    )


def _initial_buildable_locations() -> tuple[
    set[entities.Coordinate], set[entities.Coordinate]
]:
    free_verticies: set[entities.Coordinate] = set()
    free_edges: set[entities.Coordinate] = set()
    for q, r, d in itertools.product(range(-2, 3), range(-2, 3), range(0, 6)):
        if (q, r) not in entities.INVALID_HEX_COORDINATES:
            free_verticies.add(entities.canonical_vertex(q, r, d))
            free_edges.add(entities.canonical_edge(q, r, d))
    return free_verticies, free_edges
