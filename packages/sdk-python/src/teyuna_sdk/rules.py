from collections.abc import Mapping
import collections
import random

import teyuna_core


def built_terraces(
    game: teyuna_core.Game, *, by: str
) -> tuple[teyuna_core.VertexCoordinate, ...]:
    return tuple(
        p.location
        for p in game.settlements
        if p.owner == by and p.type is teyuna_core.SettlementType.TERRACE
    )


def vertices_available_for_building(
    game: teyuna_core.Game, *, by: str
) -> tuple[teyuna_core.VertexCoordinate, ...]:
    buildable, _ = placement_sets(game)
    player_paths = {from_edge(path.location) for path in game.paths if path.owner == by}
    available: list[teyuna_core.VertexCoordinate] = []
    for vertex in buildable:
        adjacent = teyuna_core.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d)
        if any(edge in player_paths for edge in adjacent):
            available.append(to_vertex(vertex))
    return tuple(available)


def edges_available_for_building(
    game: teyuna_core.Game, *, by: str
) -> tuple[teyuna_core.EdgeCoordinate, ...]:
    occupied_vertices = {from_vertex(s.location) for s in game.settlements}
    free_vertices = teyuna_core.all_board_vertices() - occupied_vertices
    _, free_edges = placement_sets(game)
    player_settlements = {
        from_vertex(s.location) for s in game.settlements if s.owner == by
    }
    player_paths = {from_edge(path.location) for path in game.paths if path.owner == by}
    available: list[teyuna_core.EdgeCoordinate] = []
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
    game: teyuna_core.Game,
) -> tuple[teyuna_core.VertexCoordinate, ...]:
    buildable, _ = placement_sets(game)
    return tuple(to_vertex(vertex) for vertex in buildable)


def edges_for_free_placement(
    game: teyuna_core.Game,
    terrace: teyuna_core.VertexCoordinate,
) -> tuple[teyuna_core.EdgeCoordinate, ...]:
    _, free_edges = placement_sets(game)
    coord = from_vertex(terrace)
    adjacent = teyuna_core.edges_adjacent_to_vertex(coord.q, coord.r, coord.d)
    return tuple(to_edge(edge) for edge in adjacent if edge in free_edges)


def vertex_touches_desert(
    game: teyuna_core.Game,
    vertex: teyuna_core.VertexCoordinate,
) -> bool:
    desert_hexes = {
        teyuna_core.HexLocation(q=hex_tile.coordinate.q, r=hex_tile.coordinate.r)
        for hex_tile in game.map
        if hex_tile.type is teyuna_core.HexType.DESERT
    }
    coord = from_vertex(vertex)
    return bool(
        teyuna_core.hex_locations_at_vertex(coord.q, coord.r, coord.d) & desert_hexes
    )


def resources_at_vertex(
    game: teyuna_core.Game,
    vertex: teyuna_core.VertexCoordinate,
) -> frozenset[teyuna_core.ResourceCard]:
    hex_by_location = {
        teyuna_core.HexLocation(q=hex_tile.coordinate.q, r=hex_tile.coordinate.r): (
            hex_tile.type
        )
        for hex_tile in game.map
    }
    coord = from_vertex(vertex)
    resources: set[teyuna_core.ResourceCard] = set()
    for location in teyuna_core.hex_locations_at_vertex(coord.q, coord.r, coord.d):
        hex_type = hex_by_location.get(location)
        if hex_type is None:
            continue
        resource = teyuna_core.HEX_TYPE_TO_RESOURCE.get(hex_type)
        if resource is not None:
            resources.add(resource)
    return frozenset(resources)


def resources_owned_by(
    game: teyuna_core.Game, *, by: str
) -> frozenset[teyuna_core.ResourceCard]:
    owned: set[teyuna_core.ResourceCard] = set()
    for settlement in game.settlements:
        if settlement.owner == by:
            owned.update(resources_at_vertex(game, settlement.location))
    return frozenset(owned)


def from_vertex(location: teyuna_core.VertexCoordinate) -> teyuna_core.Coordinate:
    return teyuna_core.canonical_vertex(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def from_edge(location: teyuna_core.EdgeCoordinate) -> teyuna_core.Coordinate:
    return teyuna_core.canonical_edge(
        location.hex_coord.q, location.hex_coord.r, location.direction
    )


def to_vertex(coord: teyuna_core.Coordinate) -> teyuna_core.VertexCoordinate:
    return teyuna_core.VertexCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def to_edge(coord: teyuna_core.Coordinate) -> teyuna_core.EdgeCoordinate:
    return teyuna_core.EdgeCoordinate(
        hex_coord=teyuna_core.HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def placement_sets(
    game: teyuna_core.Game,
) -> tuple[set[teyuna_core.Coordinate], set[teyuna_core.Coordinate]]:
    """Return (buildable_vertices, free_edges).

    buildable_vertices = free vertices minus restricted (adjacent to settlements).
    free_edges = board edges without a path.
    """
    occupied_vertices = {from_vertex(s.location) for s in game.settlements}
    occupied_edges = {from_edge(p.location) for p in game.paths}

    restricted: set[teyuna_core.Coordinate] = set()
    for settlement in game.settlements:
        restricted.update(
            teyuna_core.restricted_vertices_for(from_vertex(settlement.location))
        )

    free_vertices = teyuna_core.all_board_vertices() - occupied_vertices
    buildable = free_vertices - restricted
    free_edges = teyuna_core.all_board_edges() - occupied_edges
    return buildable, free_edges


def _can_add_path_at(
    *,
    target: teyuna_core.Coordinate,
    free_edges: set[teyuna_core.Coordinate],
    existing_settlements: set[teyuna_core.Coordinate],
    existing_paths: set[teyuna_core.Coordinate],
    free_vertices: set[teyuna_core.Coordinate],
) -> bool:
    if target not in free_edges:
        return False
    for vertex in teyuna_core.vertices_of_edge(target):
        if vertex in existing_settlements:
            return True
        if vertex in free_vertices:
            for edge in teyuna_core.edges_adjacent_to_vertex(
                vertex.q, vertex.r, vertex.d
            ):
                if edge != target and edge in existing_paths:
                    return True
    return False


def can_afford(
    resources: Mapping[teyuna_core.ResourceCard, int],
    cost: Mapping[teyuna_core.ResourceCard, int],
) -> bool:
    for resource, amount in cost.items():
        if resources.get(resource, 0) < amount:
            return False
    return True


def pick_discard(
    resources: Mapping[teyuna_core.ResourceCard, int],
    required: int,
    rng: random.Random,
) -> dict[teyuna_core.ResourceCard, int]:
    pool: list[teyuna_core.ResourceCard] = [
        resource for resource, amount in resources.items() for _ in range(amount)
    ]
    rng.shuffle(pool)
    count: collections.Counter[teyuna_core.ResourceCard] = collections.Counter()
    for resource in pool[:required]:
        count[resource] += 1
    return dict(count)
