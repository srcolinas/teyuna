import datetime

from src.game import actions, entities
from src.game.actions.handlers import _placement


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    other = game.turn_order[0]

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=other, terrace=terrace, path=path),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.settlement is None
    assert result.path is None
    assert result.next_player == ""


def test_raises_when_terrace_invalid(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
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

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_terrace_already_occupied(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_vertex(game.turn_order[0], terrace, entities.SettlementType.TERRACE)
    player = game.active_player
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
    )

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_invalid(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = entities.canonical_edge(1, 1, 1)
    assert terrace not in entities.vertices_of_edge(path)
    player = game.active_player
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_raises_when_path_already_taken(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_edge(game.turn_order[0], path)
    player = game.active_player
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )
    assert result.error == expected
    assert result.settlement is None
    assert result.path is None


def test_decrements_player_idx_and_stays_in_second_placement(
    game: entities.Game,
) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == len(game.players) - 2
    assert terrace not in game.free_verticies
    assert path not in game.free_edges
    assert game.players[player].settlements[terrace] is entities.SettlementType.TERRACE
    assert path in game.players[player].paths
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_returns_dice_roll_and_keeps_player_idx_after_first_player(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.DICE_ROLL
    assert result.next_player == player
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == 0
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_increments_players_resources_after_turn(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_grants_one_resource_per_adjacent_producing_hex() -> None:
    nicknames = ("player-0", "player-1", "player-2")
    game = entities.Game(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=8),
            entities.Hex(q=1, r=-1, type=entities.HexType.JUNGLE, number=5),
            entities.Hex(q=0, r=-1, type=entities.HexType.DESERT, number=7),
        ),
        conquistator_location=entities.HexLocation(q=0, r=-1),
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
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.SECOND_PLACEMENT
    assert result.next_player == game.active_player
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert sum(game.players[player].resources.values()) == 2
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18
    assert game.resource_supply[entities.ResourceCard.WOOD] == 18
