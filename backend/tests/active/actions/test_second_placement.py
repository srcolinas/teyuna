import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))

    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_second_placement(
            game,
            actions.FreePlacementAction(
                by=game.turn_order[0], terrace=terrace, path=path
            ),
        )


def test_raises_when_terrace_invalid(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    adjacent_terrace = entities.canonical_vertex(0, 0, 1)
    game.use_vertex(
        game.active_player, adjacent_terrace, entities.SettlementType.TERRACE
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_second_placement(
            game,
            actions.FreePlacementAction(
                by=game.active_player, terrace=terrace, path=path
            ),
        )


def test_raises_when_terrace_already_occupied(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_vertex(game.turn_order[0], terrace, entities.SettlementType.TERRACE)

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_second_placement(
            game,
            actions.FreePlacementAction(
                by=game.active_player, terrace=terrace, path=path
            ),
        )


def test_raises_when_path_invalid(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = entities.canonical_edge(1, 1, 1)
    assert terrace not in entities.vertices_of_edge(path)

    with pytest.raises(actions.InvalidPathLocation):
        actions.handle_second_placement(
            game,
            actions.FreePlacementAction(
                by=game.active_player, terrace=terrace, path=path
            ),
        )


def test_raises_when_path_already_taken(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_edge(game.turn_order[0], path)

    with pytest.raises(actions.InvalidPathLocation):
        actions.handle_second_placement(
            game,
            actions.FreePlacementAction(
                by=game.active_player, terrace=terrace, path=path
            ),
        )


def test_decrements_player_idx_and_stays_in_second_placement(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    phase = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert phase is actions.GamePhaseName.SECOND_PLACEMENT
    assert game.player_idx == len(game.players) - 2
    assert terrace not in game.free_verticies
    assert path not in game.free_edges
    assert game.players[player].settlements[terrace] is entities.SettlementType.TERRACE
    assert path in game.players[player].paths


def test_returns_dice_roll_and_keeps_player_idx_after_first_player(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))

    phase = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.active_player, terrace=terrace, path=path),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.player_idx == 0
