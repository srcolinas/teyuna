from src.game import actions, entities
import teyuna_core


def test_first_award_at_five_consecutive_paths(game: entities.Game) -> None:
    builder = game.active_player
    edge = _place_paths(game, builder, [(0, 0, d) for d in range(5)])

    actions.update_longest_road(game, builder, edge=edge)

    assert game.longest_road == (builder, 5)


def test_below_threshold_does_not_award(game: entities.Game) -> None:
    builder = game.active_player
    edge = _place_paths(game, builder, [(0, 0, d) for d in range(4)])

    actions.update_longest_road(game, builder, edge=edge)

    assert game.longest_road == (None, 0)


def test_steal_when_strictly_longer(game: entities.Game) -> None:
    holder = game.turn_order[1]
    stealer = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, stealer, [(0, 0, d) for d in range(6)])

    actions.update_longest_road(game, stealer, edge=edge)

    assert game.longest_road == (stealer, 6)


def test_equal_length_does_not_steal(game: entities.Game) -> None:
    holder = game.turn_order[1]
    challenger = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(5)])

    actions.update_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (holder, 5)


def test_opponent_settlement_breaks_road(game: entities.Game) -> None:
    builder = game.active_player
    opponent = game.turn_order[1]
    # Linear chain of 6 (not a cycle): longest would be 6 without a break.
    edge = _place_paths(
        game,
        builder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
    )
    # Opponent terrace at the midpoint splits into two length-3 segments.
    game.use_vertex(
        opponent,
        teyuna_core.canonical_vertex(0, 0, 3),
        teyuna_core.SettlementType.TERRACE,
    )

    actions.update_longest_road(game, builder, edge=edge)

    # The longest road is unassigned because no player has a road
    # that is longer or equal to 5
    assert game.longest_road == (None, 0)


def test_computation_over_no_loops_or_cycles(game: entities.Game) -> None:
    op1, op2 = list(p for p in game.players.keys() if p != game.active_player)
    game.use_edge(op1, teyuna_core.canonical_edge(0, 1, 4))
    game.use_edge(op1, teyuna_core.canonical_edge(0, 1, 3))
    game.use_edge(op2, teyuna_core.canonical_edge(1, 0, 5))
    game.use_edge(op2, teyuna_core.canonical_edge(1, 0, 0))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(0, 0, 0))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(0, 0, 5))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(0, 0, 4))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(0, 0, 3))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(0, 0, 2))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(1, 0, 3))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(1, 0, 2))
    game.use_edge(game.active_player, teyuna_core.canonical_edge(1, 0, 1))
    actions.update_longest_road(
        game, game.active_player, edge=teyuna_core.canonical_edge(1, 0, 1)
    )
    assert game.longest_road == (game.active_player, 8)


def test_when_potential_longest_road_is_blocked_by_opponent_settlement(
    game: entities.Game,
) -> None:
    # GIVEN: the current player has two disconnected roads that would
    # become the longest if they were connected
    builder = game.active_player
    _place_paths(game, builder, [(0, 0, 0), (0, -1, 0), (0, -1, 1)], terrace=(0, 0, 0))
    _place_paths(game, builder, [(0, 0, 2), (0, 0, 3)], terrace=(0, 0, 4))

    # GIVEN: an opponent in the middle of a potential longest road
    opponent = game.turn_order[1]
    _place_paths(game, opponent, [(1, 0, 3)], terrace=(0, 0, 3))

    # WHEN: the pieces that would connect two roads if it were not blocked
    # by the opponent's settlement are added
    new = teyuna_core.canonical_edge(0, 0, 1)
    game.use_edge(builder, new)
    actions.update_longest_road(game, builder, edge=new)

    # THEN: the longest road should remain unassiged because of the
    # opponent's settlement.
    assert game.longest_road == (None, 0)


def test_uses_longest_branch(
    game: entities.Game,
) -> None:
    builder = game.active_player
    # Chain of 4 around the hex plus a side branch at vertex (0, 0, 1).
    # Six edges total, but longest continuous path is 5.
    edge = _place_paths(
        game,
        builder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (1, -1, 2)],
        terrace=(0, 0, 0),
    )

    actions.update_longest_road(game, builder, edge=edge)

    assert game.longest_road == (builder, 5)


def test_holder_length_updates_when_road_grows(game: entities.Game) -> None:
    holder = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, holder, [(0, 0, d) for d in range(6)])

    actions.update_longest_road(game, holder, edge=edge)

    assert game.longest_road == (holder, 6)


def test_recompute_with_no_break_leaves_award_unchanged(game: entities.Game) -> None:
    # GIVEN: a holder of the longest road
    holder = game.turn_order[1]
    _place_paths(game, holder, [(0, 0, d) for d in range(5)], terrace=(0, 0, 1))
    game.longest_road = (holder, 5)

    # AND: an opponent with a settlement that doesn't break the longest road
    opponent = game.active_player
    vertex = teyuna_core.canonical_vertex(0, 0, 5)
    game.use_vertex(
        opponent,
        vertex,
        teyuna_core.SettlementType.TERRACE,
    )
    # WHEN: the longest road is updated regardless of the player
    actions.recompute_longest_road(
        game,
        vertex=vertex,
    )

    # THEN: the longest road should remain unchanged
    assert game.longest_road == (holder, 5)


def test_recompute_clears_award_when_holder_split_below_threshold(
    game: entities.Game,
) -> None:
    # GIVEN: a player who holds the longest road
    holder = next(p for p in game.players.keys() if p != game.active_player)
    _place_paths(
        game,
        holder,
        [(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        terrace=(0, 0, 1),
    )
    game.longest_road = (holder, 6)

    # WHEN: a player places a settlement that breaks such a road into two
    # segments, each below five pieces.
    breaker = game.active_player
    vertex = teyuna_core.canonical_vertex(0, 0, 4)
    game.use_vertex(
        breaker,
        vertex,
        teyuna_core.SettlementType.TERRACE,
    )

    actions.recompute_longest_road(game, vertex=vertex)

    # THEN: the longest road is unassigned
    assert game.longest_road == (None, 0)


def test_recompute_awards_unique_leader_after_break(game: entities.Game) -> None:
    holder, breaker, leader = list(game.players.keys())
    # GIVEN: a player who holds the longest road
    _place_paths(
        game,
        holder,
        [(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        terrace=(0, 0, 1),
    )
    game.longest_road = (holder, 6)

    # AND: a player who would have the longest road if the current holder
    # longest road was broken.
    _place_paths(
        game,
        leader,
        list((2, -1, d) for d in range(5)),
        terrace=(2, -1, 0),
    )

    # AND: another player places a settlement that breaks the current holder's
    # longest road into two segments, each below the second longest road size.
    vertex = teyuna_core.canonical_vertex(0, 0, 4)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)

    # WHEN: the longest road is recomputed
    actions.recompute_longest_road(game, vertex=vertex)

    # THEN: the longest road should be awarded to the player who had
    # the second longest road.
    assert game.longest_road == (leader, 5)


def test_recompute_clears_on_tie_for_longest(game: entities.Game) -> None:
    holder, first, second = list(game.players.keys())
    # GIVEN: a player who holds the longest road
    _place_paths(
        game,
        holder,
        [(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        terrace=(0, 0, 1),
    )
    game.longest_road = (holder, 6)

    # AND: two players with a tie in longest road length, each obove threshold
    _place_paths(
        game,
        first,
        list((2, -1, d) for d in range(5)),
        terrace=(2, -1, 0),
    )
    _place_paths(
        game,
        second,
        list((-1, 2, d) for d in range(5)),
        terrace=(-1, 2, 0),
    )

    breaker = first
    # AND: any player places a settlement that breaks the current holder's
    # longest road into two segments, each below the second longest road size.
    vertex = teyuna_core.canonical_vertex(0, 0, 4)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)

    # WHEN: the longest road is recomputed
    actions.recompute_longest_road(game, vertex=vertex)

    # THEN: the longest road should remain unassigned and the length
    # should set to the tie value.
    assert game.longest_road == (None, 5)


def test_longest_path_remains_unassigned_if_tie_is_not_broken(
    game: entities.Game,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(5)])
    actions.update_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (None, 5)


def test_longest_path_is_assigned_after_beating_tie(
    game: entities.Game,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(6)])
    actions.update_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (challenger, 6)


def test_recompute_keeps_holder_when_still_holds_longest_road_when_divided(
    game: entities.Game,
) -> None:

    holder, breaker, _ = list(game.players.keys())
    # GIVEN: a player who holds the longest road
    _place_paths(
        game,
        holder,
        [(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        terrace=(0, 0, 0),
    )
    game.longest_road = (holder, 6)

    # WHEN: another player places a settlement that breaks the current holder's
    # longest road into two segments, but the road is still longer than any other
    vertex = teyuna_core.canonical_vertex(0, 0, 2)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)

    # AND: the longest road is recomputed
    actions.recompute_longest_road(game, vertex=vertex)

    # THEN: the longest road should still be held by the original holder,
    # but the length should be updated to the new length.
    assert game.longest_road == (holder, 5)


def test_recompute_keeps_holder_when_still_holds_longest_road_when_isolated(
    game: entities.Game,
) -> None:

    holder, breaker, _ = list(game.players.keys())
    # GIVEN: a player who holds the longest road
    _place_paths(
        game,
        holder,
        [(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        terrace=(0, 0, 0),
    )
    game.longest_road = (holder, 6)

    # AND: the player also holds the second longest road
    _place_paths(
        game,
        holder,
        list((2, -1, d) for d in range(5)),
        terrace=(2, -1, 0),
    )

    # WHEN: another player places a settlement that breaks the current holder's
    # longest road into two segments, each below the second longest road size.
    vertex = teyuna_core.canonical_vertex(0, 0, 4)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)

    # AND: the longest road is recomputed
    actions.recompute_longest_road(game, vertex=vertex)

    # THEN: the longest road should still be held by the original holder,
    # but the length should be updated to the new length.
    assert game.longest_road == (holder, 5)


def _place_paths(
    game: entities.Game,
    nickname: str,
    edges: list[tuple[int, int, int]],
    *,
    terrace: tuple[int, int, int] | None = None,
) -> teyuna_core.Coordinate:
    """Place a seed terrace then paths so board sets stay consistent."""
    if terrace is None:
        q, r, d = edges[0]
        terrace = (q, r, d)
    tq, tr, td = terrace
    game.use_vertex(
        nickname,
        teyuna_core.canonical_vertex(tq, tr, td),
        teyuna_core.SettlementType.TERRACE,
    )

    last = teyuna_core.canonical_edge(*edges[0])
    game.use_edge(nickname, last)
    for q, r, d in edges[1:]:
        last = teyuna_core.canonical_edge(q, r, d)
        game.use_edge(nickname, last)
    return last
