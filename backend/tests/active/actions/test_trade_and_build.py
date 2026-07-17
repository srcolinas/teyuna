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
