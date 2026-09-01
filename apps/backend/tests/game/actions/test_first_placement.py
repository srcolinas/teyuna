import random
from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    other = game.turn_order[1]

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=other, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.settlement is None
    assert result.path is None
    assert result.next_player == ""


def test_raises_when_terrace_invalid(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    adjacent_terrace = teyuna_core.canonical_vertex(0, 0, 1)
    game.use_vertex(
        game.active_player, adjacent_terrace, teyuna_core.SettlementType.TERRACE
    )
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_terrace_already_occupied(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    game.use_vertex(game.turn_order[1], terrace, teyuna_core.SettlementType.TERRACE)
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_invalid(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = teyuna_core.canonical_edge(1, 1, 1)
    player = game.active_player
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_already_taken(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    game.use_edge(game.turn_order[1], path)
    player = game.active_player
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_mutates_board_and_advances_player(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.FIRST_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == 1
    assert terrace not in game.free_verticies
    assert path not in game.free_edges
    assert (
        game.players[player].settlements[terrace] is teyuna_core.SettlementType.TERRACE
    )
    assert path in game.players[player].paths
    assert game.restricted_verticies


def test_returns_second_placement_after_last_player(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_first_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == len(game.players) - 1
