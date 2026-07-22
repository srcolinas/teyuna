from collections.abc import Mapping

import teyuna_shared


def built_terraces(
    game: teyuna_shared.Game, *, by: str
) -> tuple[teyuna_shared.VertexCoordinate, ...]:
    return tuple(
        p.location
        for p in game.settlements
        if p.owner == by and p.type is teyuna_shared.SettlementType.TERRACE
    )


def vertices_available_for_building(
    game: teyuna_shared.Game, *, by: str
) -> tuple[teyuna_shared.VertexCoordinate, ...]:
    buildable, _ = placement_sets(game)
    player_paths = {from_edge(path.location) for path in game.paths if path.owner == by}
    available: list[teyuna_shared.VertexCoordinate] = []
    for vertex in buildable:
        adjacent = teyuna_shared.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d)
        if any(edge in player_paths for edge in adjacent):
            available.append(to_vertex(vertex))
    return tuple(available)


def edges_available_for_building(
    game: teyuna_shared.Game, *, by: str
) -> tuple[teyuna_shared.EdgeCoordinate, ...]:
    occupied_vertices = {from_vertex(s.location) for s in game.settlements}
    free_vertices = teyuna_shared.all_board_vertices() - occupied_vertices
    _, free_edges = placement_sets(game)
    player_settlements = {
        from_vertex(s.location) for s in game.settlements if s.owner == by
    }
    player_paths = {from_edge(path.location) for path in game.paths if path.owner == by}
    available: list[teyuna_shared.EdgeCoordinate] = []
    for edge in free_edges:
        if _can_add_path_at(
            target=edge,
            free_edges=free_edges,
            existing_settlements=player_settlements,
            existing_paths=player_paths,
            free_vertices=free_vertices,
        ):
            available.append(to_edge(edge))
    return tuple(available)


def vertices_available_for_free_placement(
    game: teyuna_shared.Game,
) -> tuple[teyuna_shared.VertexCoordinate, ...]:
    buildable, _ = placement_sets(game)
    return tuple(to_vertex(vertex) for vertex in buildable)


def edges_for_free_placement(
    game: teyuna_shared.Game,
    terrace: teyuna_shared.VertexCoordinate,
) -> tuple[teyuna_shared.EdgeCoordinate, ...]:
    _, free_edges = placement_sets(game)
    coord = from_vertex(terrace)
    adjacent = teyuna_shared.edges_adjacent_to_vertex(coord.q, coord.r, coord.d)
    return tuple(to_edge(edge) for edge in adjacent if edge in free_edges)


def vertex_touches_desert(
    game: teyuna_shared.Game,
    vertex: teyuna_shared.VertexCoordinate,
) -> bool:
    desert_hexes = {
        teyuna_shared.HexLocation(q=hex_tile.coordinate.q, r=hex_tile.coordinate.r)
        for hex_tile in game.map
        if hex_tile.type is teyuna_shared.HexType.DESERT
    }
    coord = from_vertex(vertex)
    return bool(
        teyuna_shared.hex_locations_at_vertex(coord.q, coord.r, coord.d) & desert_hexes
    )


def from_vertex(location: teyuna_shared.VertexCoordinate) -> teyuna_shared.Coordinate:
    return teyuna_shared.canonical_vertex(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def from_edge(location: teyuna_shared.EdgeCoordinate) -> teyuna_shared.Coordinate:
    return teyuna_shared.canonical_edge(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def to_vertex(coord: teyuna_shared.Coordinate) -> teyuna_shared.VertexCoordinate:
    return teyuna_shared.VertexCoordinate(
        hex_coord=teyuna_shared.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def to_edge(coord: teyuna_shared.Coordinate) -> teyuna_shared.EdgeCoordinate:
    return teyuna_shared.EdgeCoordinate(
        hex_coord=teyuna_shared.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def placement_sets(
    game: teyuna_shared.Game,
) -> tuple[set[teyuna_shared.Coordinate], set[teyuna_shared.Coordinate]]:
    """Return (buildable_vertices, free_edges).

    buildable_vertices = free vertices minus restricted (adjacent to settlements).
    free_edges = board edges without a path.
    """
    occupied_vertices = {from_vertex(s.location) for s in game.settlements}
    occupied_edges = {from_edge(p.location) for p in game.paths}

    restricted: set[teyuna_shared.Coordinate] = set()
    for settlement in game.settlements:
        restricted.update(
            teyuna_shared.restricted_vertices_for(from_vertex(settlement.location))
        )

    free_vertices = teyuna_shared.all_board_vertices() - occupied_vertices
    buildable = free_vertices - restricted
    free_edges = teyuna_shared.all_board_edges() - occupied_edges
    return buildable, free_edges


def _can_add_path_at(
    *,
    target: teyuna_shared.Coordinate,
    free_edges: set[teyuna_shared.Coordinate],
    existing_settlements: set[teyuna_shared.Coordinate],
    existing_paths: set[teyuna_shared.Coordinate],
    free_vertices: set[teyuna_shared.Coordinate],
) -> bool:
    if target not in free_edges:
        return False
    for vertex in teyuna_shared.vertices_of_edge(target):
        if vertex in existing_settlements:
            return True
        if vertex in free_vertices:
            for edge in teyuna_shared.edges_adjacent_to_vertex(
                vertex.q, vertex.r, vertex.d
            ):
                if edge != target and edge in existing_paths:
                    return True
    return False


def can_afford(
    resources: Mapping[teyuna_shared.ResourceCard, int],
    cost: Mapping[teyuna_shared.ResourceCard, int],
) -> bool:
    for resource, amount in cost.items():
        if resources.get(resource, 0) < amount:
            return False
    return True
