import random
import uuid

import teyuna_core

from teyuna_sdk import rules


def _empty_game(*, map_tiles: tuple[teyuna_core.Hex, ...]) -> teyuna_core.Game:
    return teyuna_core.Game(
        id=uuid.uuid4(),
        map=map_tiles,
        conquistator_location=teyuna_core.HexCoordinate(q=0, r=0),
        harbours=teyuna_core.grouped_harbours(),
        players=[],
        settlements=[],
        paths=[],
        turn_order=(),
        phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
        phase_deadline=None,
        available_slots=0,
    )


def test_vertex_touches_desert_when_adjacent_to_desert_hex() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.DESERT,
                number=7,
            ),
        )
    )
    vertex = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )

    assert rules.vertex_touches_desert(game, vertex) is True


def test_vertex_touches_desert_is_false_without_desert() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
        )
    )
    vertex = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )

    assert rules.vertex_touches_desert(game, vertex) is False


def test_vertices_available_for_free_placement_excludes_restricted() -> None:
    terrace = teyuna_core.PlayedSettlement(
        owner="player-0",
        location=teyuna_core.VertexCoordinate(
            hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
            direction=0,
        ),
        type=teyuna_core.SettlementType.TERRACE,
    )
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
        )
    )
    game = game.model_copy(update={"settlements": [terrace]})

    available = set(rules.vertices_available_for_free_placement(game))
    occupied = terrace.location
    restricted = {
        rules.to_vertex(coord)
        for coord in teyuna_core.restricted_vertices_for(rules.from_vertex(occupied))
    }

    assert occupied not in available
    assert available.isdisjoint(restricted)
    assert available


def test_edges_for_free_placement_returns_adjacent_free_edges() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
        )
    )
    terrace = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )
    edges = rules.edges_for_free_placement(game, terrace)
    expected = {
        rules.to_edge(edge) for edge in teyuna_core.edges_adjacent_to_vertex(0, 0, 0)
    }

    assert set(edges) == expected
    assert edges


def test_pick_discard_selects_exact_count() -> None:
    resources = {
        teyuna_core.ResourceCard.WOOD: 5,
        teyuna_core.ResourceCard.GOLD: 3,
    }
    count = rules.pick_discard(resources, required=4, rng=random.Random(0))

    assert sum(count.values()) == 4
    assert count.get(teyuna_core.ResourceCard.WOOD, 0) <= 5
    assert count.get(teyuna_core.ResourceCard.GOLD, 0) <= 3
