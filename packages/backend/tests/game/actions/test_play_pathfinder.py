from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_shared


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].settlements[terrace] = (
        teyuna_shared.SettlementType.TERRACE
    )
    other = game.turn_order[1]

    action = teyuna_shared.PlayPathfinderAction(by=other, paths=(path,))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.paths == ()


def test_trade_and_build_raises_when_player_not_in_turn(game: entities.Game) -> None:
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].settlements[terrace] = (
        teyuna_shared.SettlementType.TERRACE
    )
    other = game.turn_order[1]

    action = teyuna_shared.PlayPathfinderAction(by=other, paths=(path,))
    result = actions.handle_trade_and_build_play_pathfinder(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.paths == ()


def test_places_two_paths_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    first = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = teyuna_shared.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in teyuna_shared.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(first, second))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert result.paths == (first, second)
    assert first in game.players[player].paths
    assert second in game.players[player].paths


def test_places_two_paths_and_returns_to_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    first = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = teyuna_shared.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in teyuna_shared.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(first, second))
    result = actions.handle_trade_and_build_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.paths == (first, second)
    assert first in game.players[player].paths
    assert second in game.players[player].paths


def test_ignores_second_path_when_only_one_slot_remaining(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    first = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = teyuna_shared.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in teyuna_shared.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )
    game.players[player].paths = {
        teyuna_shared.Coordinate(q=9, r=i // 6, d=i % 6)
        for i in range(teyuna_shared.MAX_PATHS - 1)
    }

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(first, second))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert result.paths == (first,)
    assert first in game.players[player].paths
    assert second not in game.players[player].paths
    assert len(game.players[player].paths) == teyuna_shared.MAX_PATHS


def test_raises_when_path_is_invalid(game: entities.Game) -> None:
    player = game.active_player
    disconnected = teyuna_shared.canonical_edge(1, 0, 0)
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=disconnected,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(disconnected,))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.paths == ()


def test_raises_when_path_already_taken(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.use_edge(game.turn_order[1], path)
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(path,))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.paths == ()


def test_placing_paths_at_ten_vp_ends_game(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    game.players[player].played_cards[teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(path,))
    result = actions.handle_dice_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.END_GAME
    assert result.paths == (path,)


def test_placing_paths_at_ten_vp_ends_game_from_trade_and_build(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_shared.SettlementType.TERRACE
    game.players[player].played_cards[teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    action = teyuna_shared.PlayPathfinderAction(by=player, paths=(path,))
    result = actions.handle_trade_and_build_play_pathfinder(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.END_GAME
    assert result.paths == (path,)
