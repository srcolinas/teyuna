import itertools

import pytest

from src.active import entities


def _valid_hexes() -> list[tuple[int, int]]:
    return [
        (q, r)
        for q, r in itertools.product(range(-2, 3), range(-2, 3))
        if (q, r) not in entities.INVALID_HEX_COORDINATES
    ]


def _is_valid_coordinate(coord: entities.Coordinate) -> bool:
    return (
        -2 <= coord.q <= 2
        and -2 <= coord.r <= 2
        and (coord.q, coord.r) not in entities.INVALID_HEX_COORDINATES
    )


def test_canonical_vertex_always_on_valid_hex() -> None:
    for q, r in _valid_hexes():
        for d in range(6):
            assert _is_valid_coordinate(entities.canonical_vertex(q, r, d))


def test_canonical_edge_always_on_valid_hex() -> None:
    for q, r in _valid_hexes():
        for d in range(6):
            assert _is_valid_coordinate(entities.canonical_edge(q, r, d))


def test_canonical_vertex_stable_across_valid_aliases() -> None:
    for q, r in _valid_hexes():
        for d in range(6):
            expected = entities.canonical_vertex(q, r, d)
            candidates = {entities.Coordinate(q=q, r=r, d=d)} | entities.vertex_aliases(
                q, r, d
            )
            for alias in candidates:
                if not _is_valid_coordinate(alias):
                    continue
                assert entities.canonical_vertex(alias.q, alias.r, alias.d) == expected


def test_canonical_edge_stable_across_valid_aliases() -> None:
    for q, r in _valid_hexes():
        for d in range(6):
            expected = entities.canonical_edge(q, r, d)
            candidates = {
                entities.Coordinate(q=q, r=r, d=d),
                entities.edge_alias(q, r, d),
            }
            for alias in candidates:
                if not _is_valid_coordinate(alias):
                    continue
                assert entities.canonical_edge(alias.q, alias.r, alias.d) == expected


def test_canonical_vertex_prefers_on_board_over_out_of_range() -> None:
    assert entities.canonical_vertex(0, -2, 0) == entities.Coordinate(q=0, r=-2, d=0)


def test_canonical_edge_prefers_valid_hex_over_invalid() -> None:
    assert entities.canonical_edge(-2, 0, 5) == entities.Coordinate(q=-2, r=0, d=5)


def test_canonical_edge_from_invalid_hex_resolves_to_valid_alias() -> None:
    assert entities.canonical_edge(-2, -1, 2) == entities.Coordinate(q=-2, r=0, d=5)


def test_canonical_edge_raises_when_no_valid_hex() -> None:
    with pytest.raises(ValueError, match="no valid board hex"):
        entities.canonical_edge(-3, 0, 0)
