from src.game import actions, entities
from src.game.actions.handlers import _placement


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    other = game.turn_order[1]

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=other, terrace=terrace, path=path),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.settlement is None
    assert result.path is None
    assert result.next_player == ""


def test_raises_when_terrace_invalid(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    adjacent_terrace = entities.canonical_vertex(0, 0, 1)
    game.use_vertex(
        game.active_player, adjacent_terrace, entities.SettlementType.TERRACE
    )
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
    )

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_terrace_already_occupied(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_vertex(game.turn_order[1], terrace, entities.SettlementType.TERRACE)
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
    )

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_invalid(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = entities.canonical_edge(1, 1, 1)
    player = game.active_player
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_already_taken(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_edge(game.turn_order[1], path)
    player = game.active_player
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_mutates_board_and_advances_player(game: entities.Game) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.FIRST_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == 1
    assert terrace not in game.free_verticies
    assert path not in game.free_edges
    assert game.players[player].settlements[terrace] is entities.SettlementType.TERRACE
    assert path in game.players[player].paths
    assert game.restricted_verticies


def test_returns_second_placement_after_last_player(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_first_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == len(game.players) - 1
