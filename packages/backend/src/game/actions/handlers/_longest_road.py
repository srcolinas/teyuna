import teyuna_core

from ... import entities

_MIN_LONGEST_ROAD: int = 5


def update_longest_road(
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

    length = _longest_path_length_through(game, by, edge)
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
    edges = teyuna_core.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d)
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
            _longest_path_length_through(game, nickname, edge) for edge in player.paths
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


def _longest_path_length_through(
    game: entities.Game,
    by: str,
    start: teyuna_core.Coordinate,
) -> int:
    paths = game.players[by].paths
    settlements = game.players[by].settlements

    def can_traverse_vertex(vertex: teyuna_core.Coordinate) -> bool:
        return vertex in settlements or vertex in game.free_verticies

    def num_pieces(vertex: teyuna_core.Coordinate) -> int:
        if not can_traverse_vertex(vertex):
            return 0
        visited = {start}
        longest = 0
        stack: list[tuple[teyuna_core.Coordinate, int]] = [(vertex, 0)]
        while stack:
            current, length = stack.pop()
            longest = max(longest, length)
            for edge in teyuna_core.edges_adjacent_to_vertex(
                current.q, current.r, current.d
            ):
                if edge in paths and edge not in visited:
                    new_length = length + 1
                    longest = max(longest, new_length)
                    visited.add(edge)
                    # Continue from the far vertex when traversable; an edge that
                    # ends on an opponent settlement still counts above.
                    for other in teyuna_core.vertices_of_edge(edge):
                        if other != current and can_traverse_vertex(other):
                            stack.append((other, new_length))
        return longest

    v1, v2 = teyuna_core.vertices_of_edge(start)
    return max(num_pieces(v1), num_pieces(v2)) + 1
