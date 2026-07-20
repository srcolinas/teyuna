from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.turn_order[0], terrace=terrace, path=path),
    )
    assert result.succeeded is False
    assert result.settlement is None
    assert result.path is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_raises_when_terrace_invalid(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    adjacent_terrace = entities.canonical_vertex(0, 0, 1)
    game.use_vertex(
        game.active_player, adjacent_terrace, entities.SettlementType.TERRACE
    )

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.active_player, terrace=terrace, path=path),
    )
    assert result.succeeded is False
    assert result.settlement is None
    assert result.path is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


def test_raises_when_terrace_already_occupied(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_vertex(game.turn_order[0], terrace, entities.SettlementType.TERRACE)

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.active_player, terrace=terrace, path=path),
    )
    assert result.succeeded is False
    assert result.settlement is None
    assert result.path is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


def test_raises_when_path_invalid(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = entities.canonical_edge(1, 1, 1)
    assert terrace not in entities.vertices_of_edge(path)

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.active_player, terrace=terrace, path=path),
    )
    assert result.succeeded is False
    assert result.settlement is None
    assert result.path is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


def test_raises_when_path_already_taken(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    game.use_edge(game.turn_order[0], path)

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=game.active_player, terrace=terrace, path=path),
    )
    assert result.succeeded is False
    assert result.settlement is None
    assert result.path is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


def test_decrements_player_idx_and_stays_in_second_placement(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.SECOND_PLACEMENT
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
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.settlement == terrace
    assert result.path == path
    assert game.player_idx == 0
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_increments_players_resources_after_turn(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.SECOND_PLACEMENT
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_grants_one_resource_per_adjacent_producing_hex() -> None:
    nicknames = ("player-0", "player-1", "player-2")
    game = entities.ActiveGame(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=8),
            entities.Hex(q=1, r=-1, type=entities.HexType.JUNGLE, number=5),
            entities.Hex(q=0, r=-1, type=entities.HexType.DESERT, number=7),
        ),
        conquistator_location=entities.HexLocation(q=0, r=-1),
        turn_order=nicknames,
        players={
            nickname: entities.Player(
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
    )
    game.player_idx = len(game.players) - 1
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(iter(entities.edges_adjacent_to_vertex(0, 0, 0)))
    player = game.active_player

    result = actions.handle_second_placement(
        game,
        actions.FreePlacementAction(by=player, terrace=terrace, path=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.SECOND_PLACEMENT
    assert result.settlement == terrace
    assert result.path == path
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
    assert sum(game.players[player].resources.values()) == 2
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18
    assert game.resource_supply[entities.ResourceCard.WOOD] == 18
