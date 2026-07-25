import collections
import uuid
from enum import Enum

import pytest

from src.game import actions, entities
from src.game.actions.handlers import _placement
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    player = game.active_player
    other = game.turn_order[1]
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=other,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.item is None
    assert result.coordinate is None


def test_builds_terrace_spends_resources_and_stays_in_phase(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game._free_edges.discard(path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.item is teyuna_core.SettlementType.TERRACE
    assert result.coordinate == terrace
    assert (
        game.players[player].settlements[terrace] is teyuna_core.SettlementType.TERRACE
    )
    assert game.players[player].resources[teyuna_core.ResourceCard.STONE] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.COTTON] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.MAIZE] == 0


def test_builds_path_spends_resources_and_stays_in_phase(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )

    action = teyuna_core.BuildPathAction(
        by=player,
        coordinate=path,
    )
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == path
    assert path in game.players[player].paths
    assert game.players[player].resources[teyuna_core.ResourceCard.STONE] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 0


def test_builds_path_chained_from_owned_path(game: entities.Game) -> None:
    player = game.active_player
    owned_path = teyuna_core.canonical_edge(0, 0, 0)
    v0, v1 = teyuna_core.vertices_of_edge(owned_path)
    adjacent = next(
        e
        for e in teyuna_core.edges_adjacent_to_vertex(v1.q, v1.r, v1.d)
        if e != owned_path
    )
    game.players[player].paths.add(owned_path)
    game._free_edges.discard(owned_path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )

    action = teyuna_core.BuildPathAction(by=player, coordinate=adjacent)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == adjacent
    assert adjacent in game.players[player].paths
    assert game.players[player].resources[teyuna_core.ResourceCard.STONE] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.WOOD] == 0


def test_raises_invalid_path_location_when_disconnected(
    game: entities.Game,
) -> None:
    player = game.active_player
    disconnected = teyuna_core.canonical_edge(1, 1, 1)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=disconnected,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    action = teyuna_core.BuildPathAction(by=player, coordinate=disconnected)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.coordinate is None


def test_raises_invalid_path_location_when_already_taken(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.use_edge(game.turn_order[1], path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_path_location(
        target=path,
        player=player,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_edges=game.free_edges,
    )

    action = teyuna_core.BuildPathAction(by=player, coordinate=path)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.coordinate is None


def test_builds_great_terrace_upgrades_and_stays_in_phase(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 3,
            teyuna_core.ResourceCard.MAIZE: 2,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.item is teyuna_core.SettlementType.GREAT_TERRACE
    assert result.coordinate == terrace
    assert (
        game.players[player].settlements[terrace]
        is teyuna_core.SettlementType.GREAT_TERRACE
    )
    assert game.players[player].resources[teyuna_core.ResourceCard.GOLD] == 0
    assert game.players[player].resources[teyuna_core.ResourceCard.MAIZE] == 0


def test_building_terrace_to_ten_vp_ends_game(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game._free_edges.discard(path)
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.item is teyuna_core.SettlementType.TERRACE
    assert result.coordinate == terrace


def test_building_great_terrace_to_ten_vp_ends_game(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 3,
            teyuna_core.ResourceCard.MAIZE: 2,
        }
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.item is teyuna_core.SettlementType.GREAT_TERRACE
    assert result.coordinate == terrace


def test_building_path_at_ten_vp_ends_game(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )

    action = teyuna_core.BuildPathAction(by=player, coordinate=path)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.coordinate == path


def test_building_path_below_ten_vp_stays_in_phase(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 8
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )

    action = teyuna_core.BuildPathAction(by=player, coordinate=path)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == path


def test_raises_insufficient_resources_for_terrace(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Insufficient stone to build"
    assert result.item is None
    assert result.coordinate is None


def test_raises_insufficient_resources_for_great_terrace(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Insufficient gold to build"
    assert result.item is None
    assert result.coordinate is None


def test_raises_invalid_settlement_location_without_path(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
        existing_paths=player_state.paths,
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.item is None
    assert result.coordinate is None


def test_raises_invalid_settlement_location_when_restricted(
    game: entities.Game,
) -> None:
    player = game.active_player
    owned = teyuna_core.canonical_vertex(0, 0, 0)
    restricted = teyuna_core.canonical_vertex(0, 0, 1)
    game.use_vertex(game.turn_order[1], owned, teyuna_core.SettlementType.TERRACE)
    assert restricted in game.restricted_verticies
    path = next(
        iter(
            teyuna_core.edges_adjacent_to_vertex(
                restricted.q, restricted.r, restricted.d
            )
        )
    )
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_settlement_location(
        target=restricted,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
        existing_paths=player_state.paths,
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=restricted,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.item is None
    assert result.coordinate is None


def test_raises_invalid_settlement_location_when_occupied(
    game: entities.Game,
) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.use_vertex(game.turn_order[1], terrace, teyuna_core.SettlementType.TERRACE)
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
        existing_paths=player_state.paths,
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.item is None
    assert result.coordinate is None


def test_raises_when_terrace_cap_reached(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    for i in range(teyuna_core.MAX_TERRACES):
        game.players[player].settlements[
            teyuna_core.Coordinate(q=9, r=i // 6, d=i % 6)
        ] = teyuna_core.SettlementType.TERRACE

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "No terraces remaining"
    assert result.item is None
    assert result.coordinate is None


def test_raises_when_great_terrace_cap_reached(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 3,
            teyuna_core.ResourceCard.MAIZE: 2,
        }
    )
    for i in range(teyuna_core.MAX_GREAT_TERRACES):
        game.players[player].settlements[
            teyuna_core.Coordinate(q=9, r=i // 6, d=i % 6)
        ] = teyuna_core.SettlementType.GREAT_TERRACE

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "No great terraces remaining"
    assert result.item is None
    assert result.coordinate is None


def test_raises_when_upgrading_without_terrace(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 3,
            teyuna_core.ResourceCard.MAIZE: 2,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
        existing_paths=player_state.paths,
        existing_settlements=dict(player_state.settlements.items()),
        reason="You must first build a terrace at specified location.",
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.item is None
    assert result.coordinate is None


def test_raises_when_already_great_terrace(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.GREAT_TERRACE
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 3,
            teyuna_core.ResourceCard.MAIZE: 2,
        }
    )
    player_state = game.players[player]
    expected = _placement.format_invalid_settlement_location(
        target=terrace,
        player=player,
        free_vertices=game.free_verticies,
        restricted_vertices=game.restricted_verticies,
        existing_paths=player_state.paths,
        existing_settlements=dict(player_state.settlements.items()),
        reason="You have already built a great terrace at specified location.",
    )

    action = teyuna_core.BuildSettlementAction(
        by=player,
        item=teyuna_core.SettlementType.GREAT_TERRACE,
        coordinate=terrace,
    )
    result = actions.handle_build_terrace(
        game,
        action,
    )
    assert result.action == action
    assert result.error == expected
    assert result.item is None
    assert result.coordinate is None


def test_raises_when_path_cap_reached(game: entities.Game) -> None:
    player = game.active_player
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
        }
    )
    for i in range(teyuna_core.MAX_PATHS):
        game.players[player].paths.add(teyuna_core.Coordinate(q=9, r=i // 6, d=i % 6))

    action = teyuna_core.BuildPathAction(by=player, coordinate=path)
    result = actions.handle_build_path(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "No paths remaining"
    assert result.coordinate is None


def test_end_turn_advances_player_and_returns_to_dice_roll(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    player = game.active_player

    action = teyuna_core.PlayerAction(by=player)
    result = actions.handle_end_trade_and_build(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.turns_played == 1
    assert game.player_idx == 1
    assert game.active_player == game.turn_order[1]


def test_end_turn_promotes_cards_bought_this_turn(
    game: entities.Game,
) -> None:
    player = game.active_player
    card = teyuna_core.WisdomCard.WARRIOR
    game.players[player].cards_bought_this_turn[card] = 1

    action = teyuna_core.PlayerAction(by=player)
    result = actions.handle_end_trade_and_build(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.players[player].cards[card] == 1
    assert game.players[player].cards_bought_this_turn[card] == 0


def test_end_turn_wraps_to_first_player(game: entities.Game) -> None:
    game.player_idx = len(game.players) - 1
    player = game.active_player

    action = teyuna_core.PlayerAction(by=player)
    result = actions.handle_end_trade_and_build(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[0]
    assert game.player_idx == 0
    assert game.active_player == game.turn_order[0]


def test_end_turn_clears_trade_proposals(game: entities.Game) -> None:
    player = game.active_player
    game.trade_proposals = {
        uuid.uuid4(): teyuna_core.TradeProposal(
            by=player,
            offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 1}),
            request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
            to={game.turn_order[1]},
        )
    }

    action = teyuna_core.PlayerAction(by=player)
    result = actions.handle_end_trade_and_build(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.trade_proposals == {}


def test_end_turn_raises_when_player_not_in_turn(
    game: entities.Game,
) -> None:
    other = game.turn_order[1]
    action = teyuna_core.PlayerAction(by=other)
    result = actions.handle_end_trade_and_build(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.next_player == ""


@pytest.mark.parametrize(
    "card",
    [
        teyuna_core.WisdomCard.WARRIOR,
        teyuna_core.WisdomCard.WISDOM_OF_MAMO,
        teyuna_core.WisdomCard.BLESSING_OF_ALUNA,
        teyuna_core.WisdomCard.PATHFINDER,
        teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS,
    ],
)
def test_play_wisdom_card_raises_when_player_does_not_have_card(
    game: entities.Game,
    card: teyuna_core.WisdomCard,
) -> None:
    player = game.active_player
    action = teyuna_core.PlayWisdomCardAction(by=player, card=card)
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {player} does not have card {card.value}"
    assert result.card is None


def test_play_wisdom_card_raises_when_player_not_in_turn(
    game: entities.Game,
) -> None:
    game.players[game.active_player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    other = game.turn_order[1]

    action = teyuna_core.PlayWisdomCardAction(
        by=other,
        card=teyuna_core.WisdomCard.WARRIOR,
    )
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.card is None


def test_play_wisdom_card_raises_when_card_cannot_be_played(
    game: entities.Game,
) -> None:
    player = game.active_player

    class _UnplayableCard(str, Enum):
        UNKNOWN = "unknown card"

    unknown_card = _UnplayableCard.UNKNOWN
    game.players[player].cards[unknown_card] = 1  # type: ignore[index]

    action = teyuna_core.PlayWisdomCardAction.model_construct(
        by=player, card=unknown_card
    )
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert (
        result.error
        == "Card 'unknown card' cannot be played during the trade and build phase."
    )
    assert result.card is None


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            teyuna_core.WisdomCard.WARRIOR,
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
        ),
        (
            teyuna_core.WisdomCard.WISDOM_OF_MAMO,
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        ),
        (
            teyuna_core.WisdomCard.BLESSING_OF_ALUNA,
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
        ),
        (
            teyuna_core.WisdomCard.PATHFINDER,
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
        ),
        (
            teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS,
            teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_play_wisdom_card_transitions_to_expected_phase(
    game: entities.Game,
    card: teyuna_core.WisdomCard,
    expected_phase: teyuna_core.GamePhaseName,
) -> None:
    player = game.active_player
    game.players[player].cards[card] = 1

    action = teyuna_core.PlayWisdomCardAction(by=player, card=card)
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is expected_phase
    assert result.card is card
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1


def test_playing_legacy_to_ten_vp_ends_game(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 9

    action = teyuna_core.PlayWisdomCardAction(
        by=player, card=teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
    )
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.card is teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
    assert (
        game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS]
        == 10
    )


def test_playing_third_warrior_claims_biggest_army(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 2

    action = teyuna_core.PlayWisdomCardAction(
        by=player, card=teyuna_core.WisdomCard.WARRIOR
    )
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (player, 3)


_WISDOM_CARD_COST = {
    teyuna_core.ResourceCard.GOLD: 1,
    teyuna_core.ResourceCard.COTTON: 1,
    teyuna_core.ResourceCard.MAIZE: 1,
}


def test_buy_wisdom_card_spends_resources_and_draws_top(
    game: entities.Game,
) -> None:
    player = game.active_player
    card = teyuna_core.WisdomCard.WARRIOR
    game.wisdom_deck = [teyuna_core.WisdomCard.PATHFINDER, card]
    game.players[player].resources.update(_WISDOM_CARD_COST)
    supply_before = {
        resource: game.resource_supply[resource] for resource in _WISDOM_CARD_COST
    }

    action = teyuna_core.BuyWisdomCardAction(by=player)
    result = actions.handle_buy_wisdom_card(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.card is card
    assert game.wisdom_deck == [teyuna_core.WisdomCard.PATHFINDER]
    assert game.players[player].cards_bought_this_turn[card] == 1
    assert game.players[player].cards[card] == 0
    for resource in _WISDOM_CARD_COST:
        assert game.players[player].resources[resource] == 0
        assert game.resource_supply[resource] == supply_before[resource] + 1


def test_buy_wisdom_card_raises_when_insufficient_resources(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.wisdom_deck = [teyuna_core.WisdomCard.WARRIOR]
    game.players[player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 1,
            teyuna_core.ResourceCard.COTTON: 0,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )

    action = teyuna_core.BuyWisdomCardAction(by=player)
    result = actions.handle_buy_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Insufficient cotton to build"
    assert result.card is None


def test_buy_wisdom_card_raises_when_deck_is_empty(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.wisdom_deck = []
    game.players[player].resources.update(_WISDOM_CARD_COST)

    action = teyuna_core.BuyWisdomCardAction(by=player)
    result = actions.handle_buy_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "Cannot buy more wisdom cards"
    assert result.card is None


def test_buy_wisdom_card_raises_when_player_not_in_turn(
    game: entities.Game,
) -> None:
    other = game.turn_order[1]
    game.wisdom_deck = [teyuna_core.WisdomCard.WARRIOR]
    game.players[other].resources.update(_WISDOM_CARD_COST)

    action = teyuna_core.BuyWisdomCardAction(by=other)
    result = actions.handle_buy_wisdom_card(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.card is None
