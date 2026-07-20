import collections
import uuid
from enum import Enum

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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=game.turn_order[1],
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.item is entities.SettlementType.TERRACE
    assert result.coordinate == terrace
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

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(
            by=player,
            coordinate=path,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == path
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

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=adjacent),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == adjacent
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

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=disconnected),
    )
    assert result.succeeded is False
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


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

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=path),
    )
    assert result.succeeded is False
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidPathLocation


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.item is entities.SettlementType.GREAT_TERRACE
    assert result.coordinate == terrace
    assert (
        game.players[player].settlements[terrace]
        is entities.SettlementType.GREAT_TERRACE
    )
    assert game.players[player].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[player].resources[entities.ResourceCard.MAIZE] == 0


def test_building_terrace_to_ten_vp_ends_game(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)
    game._free_edges.discard(path)
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
    assert result.item is entities.SettlementType.TERRACE
    assert result.coordinate == terrace


def test_building_great_terrace_to_ten_vp_ends_game(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
    assert result.item is entities.SettlementType.GREAT_TERRACE
    assert result.coordinate == terrace


def test_building_path_at_ten_vp_ends_game(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
    assert result.coordinate == path


def test_building_path_below_ten_vp_stays_in_phase(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 8
    game.players[player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=path),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.coordinate == path


def test_raises_insufficient_resources_for_terrace(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[player].paths.add(path)

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=restricted,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_raises_when_upgrading_without_terrace(game: entities.ActiveGame) -> None:
    player = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


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

    result = actions.handle_build_terrace(
        game,
        actions.BuildSettlementAction(
            by=player,
            item=entities.SettlementType.GREAT_TERRACE,
            coordinate=terrace,
        ),
    )
    assert result.succeeded is False
    assert result.item is None
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidSettlementLocation


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

    result = actions.handle_build_path(
        game,
        actions.BuildPathAction(by=player, coordinate=path),
    )
    assert result.succeeded is False
    assert result.coordinate is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_end_turn_advances_player_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    game.player_idx = 0
    player = game.active_player

    result = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.player_idx == 1
    assert game.active_player == game.turn_order[1]


def test_end_turn_promotes_cards_bought_this_turn(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    card = entities.WisdomCard.WARRIOR
    game.players[player].cards_bought_this_turn[card] = 1

    result = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.players[player].cards[card] == 1
    assert game.players[player].cards_bought_this_turn[card] == 0


def test_end_turn_wraps_to_first_player(game: entities.ActiveGame) -> None:
    game.player_idx = len(game.players) - 1
    player = game.active_player

    result = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[0]
    assert game.player_idx == 0
    assert game.active_player == game.turn_order[0]


def test_end_turn_clears_trade_proposals(game: entities.ActiveGame) -> None:
    player = game.active_player
    game.trade_proposals = {
        uuid.uuid4(): entities.TradeProposal(
            by=player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={game.turn_order[1]},
        )
    }

    result = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.next_player == game.turn_order[1]
    assert game.trade_proposals == {}


def test_end_turn_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    result = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=game.turn_order[1]),
    )
    assert result.succeeded is False
    assert result.next_player == ""
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


@pytest.mark.parametrize(
    "card",
    [
        entities.WisdomCard.WARRIOR,
        entities.WisdomCard.WINDOM_OF_MAMO,
        entities.WisdomCard.BLESSING_OF_ALUNA,
        entities.WisdomCard.PATHFINDER,
        entities.WisdomCard.LEGACY_OF_THE_ELDERS,
    ],
)
def test_play_wisdom_card_raises_when_player_does_not_have_card(
    game: entities.ActiveGame,
    card: entities.WisdomCard,
) -> None:
    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=game.active_player, card=card),
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerDoesNotHaveCardError


def test_play_wisdom_card_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1

    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(
            by=game.turn_order[1],
            card=entities.WisdomCard.WARRIOR,
        ),
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_play_wisdom_card_raises_when_card_cannot_be_played(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    class _UnplayableCard(str, Enum):
        UNKNOWN = "unknown card"

    unknown_card = _UnplayableCard.UNKNOWN
    game.players[player].cards[unknown_card] = 1  # type: ignore[index]

    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=unknown_card),  # type: ignore[arg-type]
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.ActionNotAllowedError


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            entities.WisdomCard.WARRIOR,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
        ),
        (
            entities.WisdomCard.WINDOM_OF_MAMO,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        ),
        (
            entities.WisdomCard.BLESSING_OF_ALUNA,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
        ),
        (
            entities.WisdomCard.PATHFINDER,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
        ),
        (
            entities.WisdomCard.LEGACY_OF_THE_ELDERS,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_play_wisdom_card_transitions_to_expected_phase(
    game: entities.ActiveGame,
    card: entities.WisdomCard,
    expected_phase: actions.GamePhaseName,
) -> None:
    player = game.active_player
    game.players[player].cards[card] = 1

    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=card),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is expected_phase
    assert result.card is card
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1


def test_playing_legacy_to_ten_vp_ends_game(game: entities.ActiveGame) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9

    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(
            by=player, card=entities.WisdomCard.LEGACY_OF_THE_ELDERS
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
    assert result.card is entities.WisdomCard.LEGACY_OF_THE_ELDERS
    assert (
        game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS]
        == 10
    )


def test_playing_third_warrior_claims_biggest_army(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 2

    result = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
    assert result.card is entities.WisdomCard.WARRIOR
    assert game.biggest_army == (player, 3)


_WISDOM_CARD_COST = {
    entities.ResourceCard.GOLD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}


def test_buy_wisdom_card_spends_resources_and_draws_top(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    card = entities.WisdomCard.WARRIOR
    game.wisdom_deck = [entities.WisdomCard.PATHFINDER, card]
    game.players[player].resources.update(_WISDOM_CARD_COST)
    supply_before = {
        resource: game.resource_supply[resource] for resource in _WISDOM_CARD_COST
    }

    result = actions.handle_buy_wisdom_card(
        game,
        actions.BuyWisdomCardAction(by=player),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.card is card
    assert game.wisdom_deck == [entities.WisdomCard.PATHFINDER]
    assert game.players[player].cards_bought_this_turn[card] == 1
    assert game.players[player].cards[card] == 0
    for resource in _WISDOM_CARD_COST:
        assert game.players[player].resources[resource] == 0
        assert game.resource_supply[resource] == supply_before[resource] + 1


def test_buy_wisdom_card_raises_when_insufficient_resources(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    game.players[player].resources.update(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        }
    )

    result = actions.handle_buy_wisdom_card(
        game,
        actions.BuyWisdomCardAction(by=player),
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_buy_wisdom_card_raises_when_deck_is_empty(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.wisdom_deck = []
    game.players[player].resources.update(_WISDOM_CARD_COST)

    result = actions.handle_buy_wisdom_card(
        game,
        actions.BuyWisdomCardAction(by=player),
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.EmptyWisdomDeckError


def test_buy_wisdom_card_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    game.players[game.turn_order[1]].resources.update(_WISDOM_CARD_COST)

    result = actions.handle_buy_wisdom_card(
        game,
        actions.BuyWisdomCardAction(by=game.turn_order[1]),
    )
    assert result.succeeded is False
    assert result.card is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError
