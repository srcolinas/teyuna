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
    # Strictly longer than the stored record — including an unassigned tie length.
    if length > stored:
        game.longest_road = (by, length)
        if holder != by:
            return (by, length)
    return None


def recompute_longest_road(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    vertex: entities.Coordinate,
) -> tuple[player.Nickname | None, int] | None:
    """Recompute longest road after ``by`` places a terrace at ``vertex``.

    Short-circuits when the terrace does not break an adversary road.
    Returns ``(owner, length)`` when the holder identity changes (including
    clearance to ``None``); length-only updates for the same holder are silent.
    """
    if not _terrace_breaks_longest_road(game, by, vertex=vertex):
        return None

    best_length = 0
    leaders: list[player.Nickname] = []
    for nickname in game.players:
        length = _player_longest_path_length(game, nickname)
        if length < _MIN_LONGEST_ROAD:
            continue
        if length > best_length:
            best_length = length
            leaders = [nickname]
        elif length == best_length:
            leaders.append(nickname)

    previous_holder, _ = game.longest_road
    if len(leaders) == 1:
        new_holder = leaders[0]
        game.longest_road = (new_holder, best_length)
    else:
        # Unassigned, but keep the tied length (or 0 when nobody qualifies).
        new_holder = None
        game.longest_road = (None, best_length)

    if new_holder != previous_holder:
        return game.longest_road
    return None


def _terrace_breaks_longest_road(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    vertex: entities.Coordinate,
) -> bool:
    """True when exactly two adjacent edges belong to one adversary and one to ``by``."""
    owners: list[player.Nickname | None] = []
    for edge in entities.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d):
        owner: player.Nickname | None = None
        for nickname, player_state in game.players.items():
            if edge in player_state.paths:
                owner = nickname
                break
        owners.append(owner)

    builder_count = sum(1 for owner in owners if owner == by)
    if builder_count != 1:
        return False

    adversary_edges = [owner for owner in owners if owner is not None and owner != by]
    if len(adversary_edges) != 2:
        return False
    return adversary_edges[0] == adversary_edges[1]


def _player_longest_path_length(
    game: entities.ActiveGame,
    by: player.Nickname,
) -> int:
    paths = game.players[by].paths
    if not paths:
        return 0
    return max(_longest_path_length_through(game, by, edge) for edge in paths)


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
