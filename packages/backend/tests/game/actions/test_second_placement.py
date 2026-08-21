import random
import datetime

from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    other = game.turn_order[0]

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
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
    game.player_idx = len(game.players) - 1
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
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_terrace_already_occupied(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    game.use_vertex(game.turn_order[0], terrace, teyuna_core.SettlementType.TERRACE)
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_invalid(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = teyuna_core.canonical_edge(1, 1, 1)
    assert terrace not in teyuna_core.vertices_of_edge(path)
    player = game.active_player
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_already_taken(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    game.use_edge(game.turn_order[0], path)
    player = game.active_player
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
    )

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_rejects_path_adjacent_only_to_first_placement(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    player = game.active_player
    first_terrace = teyuna_core.canonical_vertex(0, 0, 0)
    first_path = teyuna_core.canonical_edge(0, 0, 0)
    game.use_vertex(player, first_terrace, teyuna_core.SettlementType.TERRACE)
    game.use_edge(player, first_path)

    second_terrace = teyuna_core.canonical_vertex(0, -2, 2)
    network_path = teyuna_core.canonical_edge(0, 0, 1)

    action = teyuna_core.FreePlacementAction(terrace=second_terrace, path=network_path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )

    assert result.error == _placement.format_invalid_path_location(
        target=network_path,
        player=player,
    )
    assert result.settlement is None
    assert result.path is None
    assert second_terrace not in game.players[player].settlements.locations()
    assert network_path not in game.players[player].paths


def test_decrements_player_idx_and_stays_in_second_placement(
    game: entities.Game,
) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == len(game.players) - 2
    assert terrace not in game.free_verticies
    assert path not in game.free_edges
    assert (
        game.players[player].settlements[terrace] is teyuna_core.SettlementType.TERRACE
    )
    assert path in game.players[player].paths
    assert game.players[player].resources[teyuna_core.ResourceCard.GOLD] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.GOLD] == 18


def test_returns_dice_roll_and_keeps_player_idx_after_first_player(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.GOLD] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.GOLD] == 18


def test_increments_players_resources_after_turn(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[teyuna_core.ResourceCard.GOLD] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.GOLD] == 18


def test_grants_one_resource_per_adjacent_producing_hex() -> None:
    nicknames = ("player-0", "player-1", "player-2")
    game = entities.Game(
        map=(
            teyuna_core.MapHex(q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=8),
            teyuna_core.MapHex(q=1, r=-1, type=teyuna_core.HexType.JUNGLE, number=5),
            teyuna_core.MapHex(q=0, r=-1, type=teyuna_core.HexType.DESERT, number=7),
        ),
        conquistator_location=teyuna_core.HexLocation(q=0, r=-1),
        players={
            nickname: entities.Player(
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    game.player_idx = len(game.players) - 1
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(teyuna_core.Coordinate(q=0, r=0, d=0))
        )
    )
    player = game.active_player

    action = teyuna_core.FreePlacementAction(terrace=terrace, path=path)
    result = actions.handle_second_placement(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[teyuna_core.ResourceCard.GOLD] == 1
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 1
    assert sum(game.players[player].resources.values()) == 2
    assert game.resource_supply[teyuna_core.ResourceCard.GOLD] == 18
    assert game.resource_supply[teyuna_core.ResourceCard.WOOD] == 18
