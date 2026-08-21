from src.game import actions, entities
import teyuna_core

from . import helpers


def test_recompute_with_no_break_leaves_award_unchanged(game: entities.Game) -> None:
    # GIVEN: a holder of the longest road
    holder = game.turn_order[1]
    helpers.place_buildings(
        game, holder, edges=[(0, 0, d) for d in range(5)], vertices=[(0, 0, 1)]
    )
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
    helpers.place_buildings(
        game,
        holder,
        edges=[(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        vertices=[(0, 0, 1)],
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
    helpers.place_buildings(
        game,
        holder,
        edges=[(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        vertices=[(0, 0, 1)],
    )
    game.longest_road = (holder, 6)

    # AND: a player who would have the longest road if the current holder
    # longest road was broken.
    helpers.place_buildings(
        game,
        leader,
        edges=list((2, -1, d) for d in range(5)),
        vertices=[(2, -1, 0)],
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
    helpers.place_buildings(
        game,
        holder,
        edges=[(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        vertices=[(0, 0, 1)],
    )
    game.longest_road = (holder, 6)

    # AND: two players with a tie in longest road length, each obove threshold
    helpers.place_buildings(
        game,
        first,
        edges=list((2, -1, d) for d in range(5)),
        vertices=[(2, -1, 0)],
    )
    helpers.place_buildings(
        game,
        second,
        edges=list((-1, 2, d) for d in range(5)),
        vertices=[(-1, 2, 0)],
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


def test_recompute_keeps_holder_when_still_holds_longest_road_when_divided(
    game: entities.Game,
) -> None:

    holder, breaker, _ = list(game.players.keys())
    # GIVEN: a player who holds the longest road
    helpers.place_buildings(
        game,
        holder,
        edges=[(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        vertices=[(0, 0, 0)],
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
    helpers.place_buildings(
        game,
        holder,
        edges=[(0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0), (-1, 0, 5)],
        vertices=[(0, 0, 0)],
    )
    game.longest_road = (holder, 6)

    # AND: the player also holds the second longest road
    helpers.place_buildings(
        game,
        holder,
        edges=[(2, -1, d) for d in range(5)],
        vertices=[(2, -1, 0)],
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
