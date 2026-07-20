from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].settlements[terrace] = (
        entities.SettlementType.TERRACE
    )

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=game.turn_order[1], paths=(path,)),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_places_two_paths_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    first = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = entities.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in entities.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(first, second)),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert first in game.players[player].paths
    assert second in game.players[player].paths


def test_places_two_paths_and_returns_to_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    first = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = entities.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in entities.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )

    result = actions.handle_trade_and_build_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(first, second)),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert first in game.players[player].paths
    assert second in game.players[player].paths


def test_ignores_second_path_when_only_one_slot_remaining(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    first = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = entities.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in entities.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )
    game.players[player].paths = {
        entities.Coordinate(q=9, r=i // 6, d=i % 6)
        for i in range(entities.MAX_PATHS - 1)
    }

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(first, second)),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert first in game.players[player].paths
    assert second not in game.players[player].paths
    assert len(game.players[player].paths) == entities.MAX_PATHS


def test_raises_when_path_is_invalid(game: entities.ActiveGame) -> None:
    player = game.active_player
    disconnected = entities.canonical_edge(1, 0, 0)

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(disconnected,)),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


def test_raises_when_path_already_taken(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.use_edge(game.turn_order[1], path)

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(path,)),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


def test_placing_paths_at_ten_vp_ends_game(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    result = actions.handle_dice_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(path,)),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME


def test_placing_paths_at_ten_vp_ends_game_from_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )

    result = actions.handle_trade_and_build_play_pathfinder(
        game,
        actions.PlayPathfinderAction(by=player, paths=(path,)),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
