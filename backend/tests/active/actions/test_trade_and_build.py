import pytest
from enum import Enum

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


def test_end_turn_promotes_cards_bought_this_turn(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    card = entities.WisdomCard.WARRIOR
    game.players[player].cards_bought_this_turn[card] = 1

    phase = actions.handle_end_trade_and_build(
        game,
        actions.PlayerAction(by=player),
    )

    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[player].cards[card] == 1
    assert game.players[player].cards_bought_this_turn[card] == 0


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
    with pytest.raises(actions.PlayerDoesNotHaveCardError):
        actions.handle_trade_and_build_play_wisdom_card(
            game,
            actions.PlayWisdomCardAction(by=game.active_player, card=card),
        )


def test_play_wisdom_card_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1

    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_trade_and_build_play_wisdom_card(
            game,
            actions.PlayWisdomCardAction(
                by=game.turn_order[1],
                card=entities.WisdomCard.WARRIOR,
            ),
        )


def test_play_wisdom_card_raises_when_card_cannot_be_played(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    class _UnplayableCard(str, Enum):
        UNKNOWN = "unknown card"

    unknown_card = _UnplayableCard.UNKNOWN
    game.players[player].cards[unknown_card] = 1  # type: ignore[index]

    with pytest.raises(actions.ActionNotAllowedError):
        actions.handle_trade_and_build_play_wisdom_card(
            game,
            actions.PlayWisdomCardAction(by=player, card=unknown_card),  # type: ignore[arg-type]
        )


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

    phase = actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=card),
    )

    assert phase is expected_phase
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1


def test_playing_third_warrior_claims_biggest_army(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 2

    actions.handle_trade_and_build_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

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

    phase = actions.handle_buy_wisdom_card(
        game,
        actions.BuyWisdomCardAction(by=player),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
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

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_buy_wisdom_card(
            game,
            actions.BuyWisdomCardAction(by=player),
        )


def test_buy_wisdom_card_raises_when_deck_is_empty(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.wisdom_deck = []
    game.players[player].resources.update(_WISDOM_CARD_COST)

    with pytest.raises(
        actions.EmptyWisdomDeckError, match="Cannot buy more wisdom cards"
    ):
        actions.handle_buy_wisdom_card(
            game,
            actions.BuyWisdomCardAction(by=player),
        )


def test_buy_wisdom_card_raises_when_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    game.wisdom_deck = [entities.WisdomCard.WARRIOR]
    game.players[game.turn_order[1]].resources.update(_WISDOM_CARD_COST)

    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_buy_wisdom_card(
            game,
            actions.BuyWisdomCardAction(by=game.turn_order[1]),
        )
