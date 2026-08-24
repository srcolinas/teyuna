from collections.abc import Container, Set
from typing import Callable, Iterable

import teyuna_core

from ... import entities

_MIN_LONGEST_ROAD: int = 5


def maybe_add_to_longest_road(
    game: entities.Game,
    by: str,
    /,
    *,
    edge: teyuna_core.Coordinate,
) -> None:
    """Recompute longest road through ``edge`` after ``by`` places a path.

    Length-only updates for the current holder are applied silently.
    """
    if len(game.players[by].paths) < _MIN_LONGEST_ROAD:
        return

    length = longest_road_in_network(
        edge,
        player_paths=game.players[by].paths,
        traversable_vertices=set(game.players[by].settlements.locations()).union(
            game.free_verticies
        ),
    )
    if length < _MIN_LONGEST_ROAD:
        return

    _, stored = game.longest_road
    # Strictly longer than the stored record — including an unassigned tie length.
    if length > stored:
        game.longest_road = (by, length)


def recompute_longest_road(
    game: entities.Game,
    *,
    vertex: teyuna_core.Coordinate,
) -> None:
    """
    Checks how roads get affected by a new settlement at ``vertex`` and
    updates the longest road accordingly.
    """

    # NOTE: if there are less than 3 edges around the vertex, the longest road is
    # not affected, beacuse all means to get to the vertex should have been counted
    # already
    edges = teyuna_core.edges_adjacent_to_vertex(vertex)
    if len(edges) < 3:
        return None

    # NOTE: if there is only one edge affected for all players, length of the roads
    # remains unchanged.
    for nickname, player in game.players.items():
        if len(edges.intersection(player.paths)) == 2:
            break
    else:
        return

    best_length = 0
    leaders: list[str] = []
    for nickname, player in game.players.items():
        # NOTE: if the player has less than 5 paths, there is no need
        # to check the length for this player.
        if len(player.paths) < _MIN_LONGEST_ROAD:
            continue

        length = max(
            longest_road_in_network(
                edge,
                player_paths=player.paths,
                traversable_vertices=set(player.settlements.locations()).union(
                    game.free_verticies
                ),
            )
            for edge in player.paths
        )
        if length < _MIN_LONGEST_ROAD:
            continue
        if length > best_length:
            best_length = length
            leaders = [nickname]
        elif length == best_length:
            leaders.append(nickname)

    if len(leaders) == 1:
        game.longest_road = (leaders[0], best_length)
    else:
        # Unassigned, but keep the tied length (or 0 when nobody qualifies).
        game.longest_road = (None, best_length)


def longest_road_in_network(
    seed: teyuna_core.Coordinate,
    *,
    player_paths: Container[teyuna_core.Coordinate],
    traversable_vertices: Container[teyuna_core.Coordinate],
) -> int:

    network = road_network(
        seed, player_paths=player_paths, traversable_vertices=traversable_vertices
    )

    lengths = (
        longest_road_from_seed(
            edge, network=network, traversable_vertices=traversable_vertices
        )
        for edge in network
    )
    return max(lengths)


def longest_road_from_seed(
    seed: teyuna_core.Coordinate,
    *,
    network: Container[teyuna_core.Coordinate],
    traversable_vertices: Container[teyuna_core.Coordinate],
) -> int:
    # NOTE: we build a road from each of the vertices of
    # the seed edge becasue it is more convenient to do the
    # search if vertices are nodes in the graph. There is a
    # path from one node to the next if there is an edge
    # in the network between them.
    type Edge = teyuna_core.Coordinate
    type Vertex = teyuna_core.Coordinate

    type Stack = list[tuple[Edge, list[tuple[Edge, Vertex]]]]

    seen: set[Edge] = set()

    def possible_paths(vertex: Vertex) -> list[tuple[Edge, Vertex]]:
        choices: list[tuple[Edge, Vertex]] = []
        for edge in teyuna_core.edges_adjacent_to_vertex(vertex):
            if edge in network and edge not in seen:
                for v in teyuna_core.vertices_of_edge(edge):
                    if v in traversable_vertices and v != vertex:
                        choices.append((edge, v))
        return choices

    def backtrack(stack: Stack) -> int:
        max_length = 0
        # NOTE: keep track of the of the edge that led to
        # the vertex, as well as all the choices that come up
        # from that vertex
        while stack:
            edge, choices = stack[-1]
            if len(choices) == 0:
                max_length = max(max_length, len(seen))
                stack.pop()
                seen.remove(edge)
                continue
            # NOTE: if there are still choices, explore
            # one of them.
            edge, vertex = choices.pop()
            seen.add(edge)
            stack.append((edge, possible_paths(vertex)))

        return max_length

    def length_from(vertex: Vertex) -> int:
        seen.clear()
        seen.add(seed)
        return backtrack([(seed, possible_paths(vertex))])

    return max(length_from(v) for v in teyuna_core.vertices_of_edge(seed))


def road_network(
    seed: teyuna_core.Coordinate,
    *,
    player_paths: Container[teyuna_core.Coordinate],
    traversable_vertices: Container[teyuna_core.Coordinate],
) -> Set[teyuna_core.Coordinate]:
    edges_in_network = {seed}
    stack = [seed]
    while stack:
        current = stack.pop()
        for _, edge in _child_edges(
            current,
            traversable_vertices=traversable_vertices,
            key=lambda edge: edge in player_paths and edge not in edges_in_network,
        ):
            edges_in_network.add(edge)
            stack.append(edge)
    return edges_in_network


def _child_edges(
    edge: teyuna_core.Coordinate,
    *,
    traversable_vertices: Container[teyuna_core.Coordinate],
    key: Callable[[teyuna_core.Coordinate], bool],
) -> Iterable[tuple[teyuna_core.Coordinate, teyuna_core.Coordinate]]:
    for vertex in teyuna_core.vertices_of_edge(edge):
        if vertex in traversable_vertices:
            for child in teyuna_core.edges_adjacent_to_vertex(vertex):
                if child != edge and key(child):
                    yield vertex, child
