import pytest

from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    player = game.active_player
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=game.turn_order[1],
                item=entities.SettlementType.TERRACE,
                coordinate=terrace,
            ),
        )


def test_builds_terrace_spends_resources_and_stays_in_phase(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game._free_edges.discard(path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    phase = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.players[player].settlements[terrace] is entities.SettlementType.TERRACE
    assert game.players[player].resources[entities.ResourceCard.STONE] == 0
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 0
    assert game.players[player].resources[entities.ResourceCard.COTTON] == 0
    assert game.players[player].resources[entities.ResourceCard.MAIZE] == 0


def test_builds_path_spends_resources_and_stays_in_phase(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    phase = actions.handle_build_path(
        game,
        actions.BuildPathAction(
            by=player,
            coordinate=path,
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert path in game.players[player].paths
    assert game.players[player].resources[entities.ResourceCard.STONE] == 0
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 0


def test_builds_path_chained_from_owned_path(game: entities.ActiveGame) -> None:
    player = game.active_player
    owned_path = entities.canonical_edge(0, 0, 0)
    v0, v1 = entities.vertices_of_edge(owned_path)
    adjacent = next(
        e
        for e in entities.edges_adjacent_to_vertex(v1.q, v1.r, v1.d)
        if e != owned_path
    )
    game.players[player].paths.add(owned_path)
    game._free_edges.discard(owned_path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    phase = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=adjacent),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert adjacent in game.players[player].paths
    assert game.players[player].resources[entities.ResourceCard.STONE] == 0
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 0


def test_raises_invalid_path_location_when_disconnected(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    disconnected = entities.canonical_edge(1, 1, 1)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    with pytest.raises(actions.InvalidPathLocation):
        actions.handle_build_path(
            game,
            actions.BuildPathAction(by=player, coordinate=disconnected),
        )


def test_raises_invalid_path_location_when_already_taken(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.use_edge(game.turn_order[1], path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    with pytest.raises(actions.InvalidPathLocation):
        actions.handle_build_path(
            game,
            actions.BuildPathAction(by=player, coordinate=path),
        )


def test_builds_great_terrace_upgrades_and_stays_in_phase(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )

    phase = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert (
        game.players[player].settlements[terrace]
        is entities.SettlementType.GREAT_TERRACE
    )
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[player].resources[entities.ResourceCard.MAIZE] == 0


def test_raises_insufficient_resources_for_terrace(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_invalid_settlement_location_without_path(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_invalid_settlement_location_when_restricted(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    owned = entities.canonical_vertex(0, 0, 0)
    restricted = entities.canonical_vertex(0, 0, 1)
    game.use_vertex(game.turn_order[1], owned, entities.SettlementType.TERRACE)
    assert restricted in game.restricted_verticies
    path = next(
        iter(
            entities.edges_adjacent_to_vertex(restricted.q, restricted.r, restricted.d)
        )
    )
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.TERRACE,
                coordinate=restricted,
            ),
        )


def test_raises_invalid_settlement_location_when_occupied(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.use_vertex(game.turn_order[1], terrace, entities.SettlementType.TERRACE)
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_when_terrace_cap_reached(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    for i in range(entities.MAX_TERRACES):
        game.players[player].settlements[
            entities.Coordinate(q=9, r=i // 6, d=i % 6)
        ] = entities.SettlementType.TERRACE

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_when_great_terrace_cap_reached(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    for i in range(entities.MAX_GREAT_TERRACES):
        game.players[player].settlements[
            entities.Coordinate(q=9, r=i // 6, d=i % 6)
        ] = entities.SettlementType.GREAT_TERRACE

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.GREAT_TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_when_upgrading_without_terrace(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.GREAT_TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_when_already_great_terrace(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.GREAT_TERRACE
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )

    with pytest.raises(actions.InvalidSettlementLocation):
        actions.handle_build_terrace(
            game,
            actions.BuildSettlementAction(
                by=player,
                item=entities.SettlementType.GREAT_TERRACE,
                coordinate=terrace,
            ),
        )


def test_raises_when_path_cap_reached(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    for i in range(entities.MAX_PATHS):
        game.players[player].paths.add(entities.Coordinate(q=9, r=i // 6, d=i % 6))

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_build_path(
            game,
            actions.BuildPathAction(by=player, coordinate=path),
        )


def test_end_turn_advances_player_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    phase = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.player_idx == 1
    assert game.active_player == game.turn_order[1]


def test_end_turn_wraps_to_first_player(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    player = game.active_player

    phase = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.player_idx == 0
    assert game.active_player == game.turn_order[0]


def test_end_turn_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_end_trade_and_build(
            game,
            actions.PlayerAction(by=game.turn_order[1]),
        )
