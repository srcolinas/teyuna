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


def test_resources_at_vertex_three_distinct_types() -> None:
    # Vertex (0, 0, 0) meets hexes (0, 0), (1, -1), and (0, -1).
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=-1),
                type=teyuna_core.HexType.JUNGLE,
                number=6,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=-1),
                type=teyuna_core.HexType.VALLEYS,
                number=9,
            ),
        )
    )
    vertex = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )

    assert rules.resources_at_vertex(game, vertex) == frozenset(
        {
            teyuna_core.ResourceCard.GOLD,
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.MAIZE,
        }
    )


def test_resources_at_vertex_desert_and_one_producing_hex() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.DESERT,
                number=7,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=-1),
                type=teyuna_core.HexType.QUARRIES,
                number=5,
            ),
        )
    )
    vertex = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )

    assert rules.resources_at_vertex(game, vertex) == frozenset(
        {teyuna_core.ResourceCard.STONE}
    )


def test_resources_at_vertex_duplicate_types_count_once() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.JUNGLE,
                number=6,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=-1),
                type=teyuna_core.HexType.JUNGLE,
                number=4,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=-1),
                type=teyuna_core.HexType.JUNGLE,
                number=10,
            ),
        )
    )
    vertex = teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
        direction=0,
    )

    assert rules.resources_at_vertex(game, vertex) == frozenset(
        {teyuna_core.ResourceCard.WOOD}
    )


def test_resources_owned_by_empty_when_no_settlements() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
        )
    )

    assert rules.resources_owned_by(game, by="player-0") == frozenset()


def test_resources_owned_by_one_terrace() -> None:
    # Vertex (0, 0, 0) meets hexes (0, 0), (1, -1), and (0, -1).
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=-1),
                type=teyuna_core.HexType.JUNGLE,
                number=6,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=-1),
                type=teyuna_core.HexType.VALLEYS,
                number=9,
            ),
        )
    )
    terrace = teyuna_core.PlayedSettlement(
        owner="player-0",
        location=teyuna_core.VertexCoordinate(
            hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
            direction=0,
        ),
        type=teyuna_core.SettlementType.TERRACE,
    )
    game = game.model_copy(update={"settlements": [terrace]})

    assert rules.resources_owned_by(game, by="player-0") == frozenset(
        {
            teyuna_core.ResourceCard.GOLD,
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.MAIZE,
        }
    )
    assert rules.resources_owned_by(game, by="other") == frozenset()


def test_resources_owned_by_unions_multiple_terraces() -> None:
    game = _empty_game(
        map_tiles=(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=0),
                type=teyuna_core.HexType.MOUNTAINS,
                number=8,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=-1),
                type=teyuna_core.HexType.JUNGLE,
                number=6,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=0, r=-1),
                type=teyuna_core.HexType.VALLEYS,
                number=9,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=1, r=0),
                type=teyuna_core.HexType.QUARRIES,
                number=5,
            ),
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=2, r=-1),
                type=teyuna_core.HexType.HIGHLANDS,
                number=4,
            ),
        )
    )
    first = teyuna_core.PlayedSettlement(
        owner="player-0",
        location=teyuna_core.VertexCoordinate(
            hex_coord=teyuna_core.HexCoordinate(q=0, r=0),
            direction=0,
        ),
        type=teyuna_core.SettlementType.TERRACE,
    )
    # Vertex (1, 0, 0) meets hexes (1, 0), (2, -1), and (1, -1).
    second = teyuna_core.PlayedSettlement(
        owner="player-0",
        location=teyuna_core.VertexCoordinate(
            hex_coord=teyuna_core.HexCoordinate(q=1, r=0),
            direction=0,
        ),
        type=teyuna_core.SettlementType.TERRACE,
    )
    game = game.model_copy(update={"settlements": [first, second]})

    assert rules.resources_owned_by(game, by="player-0") == frozenset(
        {
            teyuna_core.ResourceCard.GOLD,
            teyuna_core.ResourceCard.WOOD,
            teyuna_core.ResourceCard.MAIZE,
            teyuna_core.ResourceCard.STONE,
            teyuna_core.ResourceCard.COTTON,
        }
    )


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
