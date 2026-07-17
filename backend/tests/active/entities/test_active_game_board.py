import pytest

from src.active import entities


def test_use_vertex_removes_settlement_vertex_from_free(
    game: entities.ActiveGame,
) -> None:
    target = entities.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, entities.SettlementType.TERRACE)

    assert target not in game.free_verticies


def test_use_vertex_assigns_to_player(
    game: entities.ActiveGame,
) -> None:
    target = entities.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, entities.SettlementType.TERRACE)
    assert game.players["player"].settlements[target] is entities.SettlementType.TERRACE


def test_use_vertex_restricts_adjacent_vertices(
    game: entities.ActiveGame,
) -> None:
    target = entities.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, entities.SettlementType.TERRACE)

    assert game.restricted_verticies == {
        entities.canonical_vertex(0, -1, 1),
        entities.canonical_vertex(0, 0, 5),
        entities.canonical_vertex(0, 0, 1),
    }


def test_use_vertex_keeps_adjacent_vertices_in_free(
    game: entities.ActiveGame,
) -> None:
    target = entities.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, entities.SettlementType.TERRACE)

    assert game.free_verticies & game.restricted_verticies == game.restricted_verticies


def test_use_edge_assigns_path_and_removes_free_edge(
    game: entities.ActiveGame,
) -> None:
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))

    game.use_edge("player", path)

    assert path not in game.free_edges
    assert path in game.players["player"].paths


@pytest.fixture
def game() -> entities.ActiveGame:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    return entities.ActiveGame(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=0, r=0),
        turn_order=("player",),
        players={"player": entities.Player()},
    )
