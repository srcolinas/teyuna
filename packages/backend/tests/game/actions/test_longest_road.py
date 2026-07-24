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

    assert game.longest_road == (None, 0)


def test_new_path_endpoint_on_opponent_settlement_skips_that_side(
    game: entities.Game,
) -> None:
    """One start endpoint is an opponent terrace → dfs returns 0 for that vertex."""
    builder = game.active_player
    opponent = game.turn_order[1]
    _place_paths(game, builder, [(0, 0, 0), (0, 0, 1)])
    # Far tip of the next path the builder will add.
    game.use_vertex(
        opponent,
        teyuna_core.canonical_vertex(0, 0, 3),
        teyuna_core.SettlementType.TERRACE,
    )

    game.use_edge(builder, teyuna_core.canonical_edge(0, 0, 2))
    start = teyuna_core.canonical_edge(0, 0, 2)
    blocked = teyuna_core.canonical_vertex(0, 0, 3)

    assert blocked in game.players[opponent].settlements
    assert blocked not in game.free_verticies
    assert blocked in teyuna_core.vertices_of_edge(start)

    actions.update_longest_road(game, builder, edge=start)

    # Opponent tip contributes 0; own side has paths (0,0,0) and (0,0,1) → 2; + start → 3.
    assert game.longest_road == (None, 0)


def test_branching_uses_longest_branch_not_edge_count(
    game: entities.Game,
) -> None:
    builder = game.active_player
    # Chain of 4 around the hex plus a side branch at vertex (0, 0, 1).
    # Five edges total, but longest continuous path is 4.
    edge = _place_paths(
        game,
        builder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (1, -1, 2)],
    )

    actions.update_longest_road(game, builder, edge=edge)

    assert game.longest_road == (None, 0)


def test_player_longest_path_length_ignores_spur_iteration_order(
    game: entities.Game,
) -> None:
    """Length must stay 8 even when a short spur edge is iterated first.

    Seeding from the spur alone yields 6 while still reaching every main-road
    edge. Skipping those visited edges would under-report 6 instead of 8.
    """
    builder = game.active_player
    main = [
        (0, -1, 1),
        (0, -1, 0),
        (0, 0, 0),
        (0, 0, 1),
        (0, 0, 2),
        (0, 0, 3),
        (0, 0, 4),
        (-1, 0, 0),
    ]
    _place_paths(game, builder, main, terrace=(0, 0, 0))
    spur = teyuna_core.canonical_edge(1, -1, 2)
    game.use_edge(builder, spur)

    # Through the spur alone the continuous length is only 6; through the main
    # road it is 8. Force spur-first iteration to catch visited-edge skips.
    actions.update_longest_road(game, builder, edge=spur)
    assert game.longest_road == (builder, 6)
    actions.update_longest_road(game, builder, edge=teyuna_core.canonical_edge(0, 0, 2))
    assert game.longest_road == (builder, 8)

    class _SpurFirstPaths(set):
        def __iter__(self):  # type: ignore[override]
            items = list(super().__iter__())
            items.sort(key=lambda edge: (edge != spur, edge))
            return iter(items)

    game.players[builder].paths = _SpurFirstPaths(game.players[builder].paths)

    assert actions.player_longest_path_length(game, builder) == 8


def test_holder_length_updates_when_road_grows(game: entities.Game) -> None:
    holder = game.active_player
    game.longest_road = (holder, 5)
    edge = _place_paths(game, holder, [(0, 0, d) for d in range(6)])

    actions.update_longest_road(game, holder, edge=edge)

    assert game.longest_road == (holder, 6)


def test_recompute_no_break_leaves_award_unchanged(game: entities.Game) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    game.longest_road = (holder, 5)
    _place_paths(game, breaker, [(0, 0, 0), (0, 0, 1)])
    vertex = teyuna_core.canonical_vertex(0, 0, 2)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)

    actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert game.longest_road == (holder, 5)


def test_recompute_clears_award_when_holder_split_below_threshold(
    game: entities.Game,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_holder_road_through_midpoint(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    vertex = teyuna_core.canonical_vertex(0, 0, 3)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)
    game.longest_road = (holder, 6)

    actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert game.longest_road == (None, 0)


def test_recompute_awards_unique_leader_after_break(game: entities.Game) -> None:
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
    vertex = teyuna_core.canonical_vertex(0, 0, 3)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)
    game.longest_road = (holder, 6)

    actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert game.longest_road == (leader, 5)


def test_recompute_clears_on_tie_for_longest(game: entities.Game) -> None:
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
    vertex = teyuna_core.canonical_vertex(0, 0, 3)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)
    game.longest_road = (holder, 8)

    actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert game.longest_road == (None, 5)


def test_path_must_beat_unassigned_tie_length_to_claim(
    game: entities.Game,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = _place_paths(game, challenger, [(0, 0, d) for d in range(5)])

    actions.update_longest_road(game, challenger, edge=edge)
    assert game.longest_road == (None, 5)

    game.use_edge(challenger, teyuna_core.canonical_edge(0, 0, 5))
    edge = teyuna_core.canonical_edge(0, 0, 5)
    actions.update_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (challenger, 6)


def test_recompute_keeps_holder_when_still_uniquely_longest(
    game: entities.Game,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_holder_road_of_eight(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    vertex = teyuna_core.canonical_vertex(0, 0, 3)
    game.use_vertex(breaker, vertex, teyuna_core.SettlementType.TERRACE)
    game.longest_road = (holder, 8)

    actions.recompute_longest_road(game, breaker, vertex=vertex)

    assert game.longest_road == (holder, 5)


def test_handle_build_path_awards_longest_road(game: entities.Game) -> None:
    player = game.active_player
    _place_paths(game, player, [(0, 0, d) for d in range(4)])
    fifth = teyuna_core.canonical_edge(0, 0, 4)
    _give_path_resources(game, player)

    action = teyuna_core.BuildPathAction(by=player, coordinate=fifth)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == fifth
    assert game.longest_road == (player, 5)
    assert fifth in game.players[player].paths


def test_handle_build_path_can_end_game_via_longest_road(
    game: entities.Game,
) -> None:
    player = game.active_player
    # Seed terrace (1) + 7 Legacy + longest road (2) = 10.
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 7
    _place_paths(game, player, [(0, 0, d) for d in range(4)])
    fifth = teyuna_core.canonical_edge(0, 0, 4)
    _give_path_resources(game, player)

    action = teyuna_core.BuildPathAction(by=player, coordinate=fifth)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.coordinate == fifth
    assert game.longest_road == (player, 5)
    assert entities.victory_points(game, player) == 10


def test_handle_build_terrace_clears_longest_road_when_breaking_holder(
    game: entities.Game,
) -> None:
    holder = game.turn_order[1]
    breaker = game.active_player
    _place_holder_road_through_midpoint(game, holder)
    _place_breaker_path_into_midpoint(game, breaker)
    game.longest_road = (holder, 6)
    vertex = teyuna_core.canonical_vertex(0, 0, 3)
    game.players[breaker].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=breaker,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=vertex,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.item is teyuna_core.SettlementType.TERRACE
    assert result.coordinate == vertex
    assert game.longest_road == (None, 0)
    assert (
        game.players[breaker].settlements[vertex] is teyuna_core.SettlementType.TERRACE
    )


def test_pathfinder_awards_longest_road_on_fifth_path(
    game: entities.Game,
) -> None:
    player = game.active_player
    _place_paths(game, player, [(0, 0, d) for d in range(3)])
    fourth = teyuna_core.canonical_edge(0, 0, 3)
    fifth = teyuna_core.canonical_edge(0, 0, 4)

    action = teyuna_core.PlayPathfinderAction(by=player, paths=(fourth, fifth))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.paths == (fourth, fifth)
    assert game.longest_road == (player, 5)
    assert fourth in game.players[player].paths
    assert fifth in game.players[player].paths


def _give_path_resources(game: entities.Game, nickname: str) -> None:
    game.players[nickname].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )


def _place_holder_road_through_midpoint(game: entities.Game, holder: str) -> None:
    _place_paths(
        game,
        holder,
        [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
    )


def _place_holder_road_of_eight(game: entities.Game, holder: str) -> None:
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


def _place_breaker_path_into_midpoint(game: entities.Game, breaker: str) -> None:
    """Connect breaker to midpoint without restricting it (seed two edges away)."""
    game.use_vertex(
        breaker,
        teyuna_core.canonical_vertex(-2, 2, 1),
        teyuna_core.SettlementType.TERRACE,
    )
    game.use_edge(breaker, teyuna_core.canonical_edge(-1, 1, 2))
    game.use_edge(breaker, teyuna_core.canonical_edge(-1, 1, 1))


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
