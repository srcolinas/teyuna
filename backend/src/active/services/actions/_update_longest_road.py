from .... import player
from ... import entities

_MIN_LONGEST_ROAD: int = 5


def update_longest_road(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    edge: entities.Coordinate,
) -> tuple[player.Nickname, int] | None:
    """Recompute longest road through ``edge``.

    Returns ``(owner, length)`` when the longest-road holder changes,
    otherwise ``None``. Length-only updates for the current holder are
    applied silently.
    """
    length = _longest_path_length_through(game, by, edge)
    if length < _MIN_LONGEST_ROAD:
        return None

    holder, stored = game.longest_road
    if holder is None or length > stored:
        game.longest_road = (by, length)
        if holder != by:
            return (by, length)
    return None


def _longest_path_length_through(
    game: entities.ActiveGame,
    by: player.Nickname,
    start: entities.Coordinate,
) -> int:
    paths = game.players[by].paths
    if start not in paths:
        raise RuntimeError(f"Start {start} is not a path")

    settlements = game.players[by].settlements
    visited_edges = {start}

    def vertex_is_valid(vertex: entities.Coordinate) -> bool:
        return vertex in settlements or vertex in game.free_verticies

    def edge_is_valid(edge: entities.Coordinate) -> bool:
        return edge in paths and edge not in visited_edges

    def dfs(vertex: entities.Coordinate) -> int:
        if not vertex_is_valid(vertex):
            return 0
        longest = 0
        stack: list[tuple[entities.Coordinate, int]] = [(vertex, 0)]
        while stack:
            current, length = stack.pop()
            longest = max(longest, length)
            for edge in entities.edges_adjacent_to_vertex(
                current.q, current.r, current.d
            ):
                if not edge_is_valid(edge):
                    continue
                new_length = length + 1
                longest = max(longest, new_length)
                visited_edges.add(edge)
                # Continue from the far vertex when traversable; an edge that
                # ends on an opponent settlement still counts above.
                for other in entities.vertices_of_edge(edge):
                    if other != current and vertex_is_valid(other):
                        stack.append((other, new_length))
        return longest

    v1, v2 = entities.vertices_of_edge(start)
    return dfs(v1) + dfs(v2) + 1
