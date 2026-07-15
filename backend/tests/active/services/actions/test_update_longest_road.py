from src.active import entities
from src.active.services import actions


def test_first_award_at_five_consecutive_paths(game: entities.ActiveGame) -> None:
    builder = game.active_player
    edge = _place_paths(game, builder, [(0, 0, d) for d in range(5)])

    result = actions.update_longest_road(game, builder, edge=edge)

    assert result == (builder, 5)
    assert game.longest_road == (builder, 5)


def test_below_threshold_does_not_award(game: entities.ActiveGame) -> None:
    builder = game.active_player
    edge = _place_paths(game, builder, [(0, 0, d) for d in range(4)])

    result = actions.update_longest_road(game, builder, edge=edge)

    assert result is None
    assert game.longest_road == (None, 0)


def test_steal_when_strictly_longer(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    stealer = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, stealer, [(0, 0, d) for d in range(6)])

    result = actions.update_longest_road(game, stealer, edge=edge)

    assert result == (stealer, 6)
    assert game.longest_road == (stealer, 6)


def test_equal_length_does_not_steal(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    challenger = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(5)])

    result = actions.update_longest_road(game, challenger, edge=edge)

    assert result is None
    assert game.longest_road == (holder, 5)


def test_opponent_settlement_breaks_road(game: entities.ActiveGame) -> None:
    builder = game.active_player
    opponent = game.turn_order[1]
    # Linear chain of 6 (not a cycle): longest would be 6 without a break.
    edge = _place_paths(
        game,
        builder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
    )
    # Opponent terrace at the midpoint splits into two length-3 segments.
    actions.add_free_terrace(game, opponent, q=0, r=0, direction=3)

    result = actions.update_longest_road(game, builder, edge=edge)

    assert result is None
    assert game.longest_road == (None, 0)


def test_new_path_endpoint_on_opponent_settlement_skips_that_side(
    game: entities.ActiveGame,
) -> None:
    """One start endpoint is an opponent terrace → dfs returns 0 for that vertex."""
    builder = game.active_player
    opponent = game.turn_order[1]
    _place_paths(game, builder, [(0, 0, 0), (0, 0, 1)])
    # Far tip of the next path the builder will add.
    actions.add_free_terrace(game, opponent, q=0, r=0, direction=3)

    actions.add_free_path(game, builder, q=0, r=0, direction=2)
    start = entities.canonical_edge(0, 0, 2)
    blocked = entities.canonical_vertex(0, 0, 3)

    assert blocked in game.players[opponent].settlements
    assert blocked not in game.free_verticies
    assert blocked in entities.vertices_of_edge(start)

    result = actions.update_longest_road(game, builder, edge=start)

    # Opponent tip contributes 0; own side has paths (0,0,0) and (0,0,1) → 2; + start → 3.
    assert result is None
    assert game.longest_road == (None, 0)


def test_branching_uses_longest_branch_not_edge_count(
    game: entities.ActiveGame,
) -> None:
    builder = game.active_player
    # Chain of 4 around the hex plus a side branch at vertex (0, 0, 1).
    # Five edges total, but longest continuous path is 4.
    edge = _place_paths(
        game,
        builder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (1, -1, 2)],
    )

    result = actions.update_longest_road(game, builder, edge=edge)

    assert result is None
    assert game.longest_road == (None, 0)


def test_holder_length_updates_when_road_grows(game: entities.ActiveGame) -> None:
    holder = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, holder, [(0, 0, d) for d in range(6)])

    result = actions.update_longest_road(game, holder, edge=edge)

    assert result is None
    assert game.longest_road == (holder, 6)


def test_recompute_no_break_leaves_award_unchanged(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    game.longest_road = (holder, 5)
    _place_paths(game, breaker, [(0, 0, 0), (0, 0, 1)])
    vertex = entities.canonical_vertex(0, 0, 2)
    actions.add_free_terrace(game, breaker, q=0, r=0, direction=2)

    result = actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert result is None
    assert game.longest_road == (holder, 5)


def test_recompute_clears_award_when_holder_split_below_threshold(
    game: entities.ActiveGame,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_holder_road_through_midpoint(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    vertex = entities.canonical_vertex(0, 0, 3)
    actions.add_free_terrace(game, breaker, q=0, r=0, direction=3)
    game.longest_road = (holder, 6)

    result = actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert result == (None, 0)
    assert game.longest_road == (None, 0)


def test_recompute_awards_unique_leader_after_break(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    leader = game.turn_order[2]
    _place_holder_road_through_midpoint(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    _place_paths(
        game,
        leader,
        [(2, -1, 0), (2, -1, 1), (2, -1, 2), (2, -1, 3), (2, -1, 4)],
        terrace=(2, -1, 0),
    )
    vertex = entities.canonical_vertex(0, 0, 3)
    actions.add_free_terrace(game, breaker, q=0, r=0, direction=3)
    game.longest_road = (holder, 6)

    result = actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert result == (leader, 5)
    assert game.longest_road == (leader, 5)


def test_recompute_clears_on_tie_for_longest(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    rival = game.turn_order[2]
    _place_holder_road_of_eight(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    _place_paths(
        game,
        rival,
        [(2, -1, 0), (2, -1, 1), (2, -1, 2), (2, -1, 3), (2, -1, 4)],
        terrace=(2, -1, 0),
    )
    vertex = entities.canonical_vertex(0, 0, 3)
    actions.add_free_terrace(game, breaker, q=0, r=0, direction=3)
    game.longest_road = (holder, 8)

    result = actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert result == (None, 5)
    assert game.longest_road == (None, 5)


def test_path_must_beat_unassigned_tie_length_to_claim(
    game: entities.ActiveGame,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(5)])

    assert actions.update_longest_road(game, challenger, edge=edge) is None
    assert game.longest_road == (None, 5)

    actions.add_free_path(game, challenger, q=0, r=0, direction=5)
    edge = entities.canonical_edge(0, 0, 5)
    result = actions.update_longest_road(game, challenger, edge=edge)

    assert result == (challenger, 6)
    assert game.longest_road == (challenger, 6)


def test_recompute_keeps_holder_when_still_uniquely_longest(
    game: entities.ActiveGame,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_holder_road_of_eight(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    vertex = entities.canonical_vertex(0, 0, 3)
    actions.add_free_terrace(game, breaker, q=0, r=0, direction=3)
    game.longest_road = (holder, 8)

    result = actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert result is None
    assert game.longest_road == (holder, 5)


def _place_holder_road_through_midpoint(game: entities.ActiveGame, holder: str) -> None:
    _place_paths(
        game,
        holder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
    )


def _place_holder_road_of_eight(game: entities.ActiveGame, holder: str) -> None:
    _place_paths(
        game,
        holder,
        [
            (0, -1, 1),
            (0, -1, 0),
            (0, 0, 0),
            (0, 0, 1),
            (0, 0, 2),
            (0, 0, 3),
            (0, 0, 4),
            (-1, 0, 0),
        ],
        terrace=(0, 0, 0),
    )


def _place_breaker_path_into_midpoint(game: entities.ActiveGame, breaker: str) -> None:
    """Connect breaker to midpoint without restricting it (seed two edges away)."""
    actions.add_free_terrace(game, breaker, q=-2, r=2, direction=1)
    actions.add_free_path(game, breaker, q=-1, r=1, direction=2)
    actions.add_free_path(game, breaker, q=-1, r=1, direction=1)


def _place_paths(
    game: entities.ActiveGame,
    nickname: str,
    edges: list[tuple[int, int, int]],
    *,
    terrace: tuple[int, int, int] | None = None,
) -> entities.Coordinate:
    """Place a seed terrace then paths via real actions so board sets stay consistent."""
    if terrace is None:
        q, r, d = edges[0]
        terrace = (q, r, d)
    tq, tr, td = terrace
    actions.add_free_terrace(game, nickname, q=tq, r=tr, direction=td)

    last = entities.canonical_edge(*edges[-1])
    for q, r, d in edges:
        actions.add_free_path(game, nickname, q=q, r=r, direction=d)
        last = entities.canonical_edge(q, r, d)
    return last
