import collections

import pytest

from src.game import actions, entities
import teyuna_core


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    game.players[other].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 4}
    )

    action = teyuna_core.TradeWithSupplyAction(
        by=other,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_cannot_trade_if_not_enough_resources_from_player(
    game: entities.Game,
) -> None:
    action = teyuna_core.TradeWithSupplyAction(
        by=game.active_player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "You do not have enough gold to offer."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_cannot_trade_if_not_enough_resources_from_supply(
    game: entities.Game,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 4}
    )
    game.resource_supply[teyuna_core.ResourceCard.STONE] = 0
    action = teyuna_core.TradeWithSupplyAction(
        by=game.active_player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "The supply does not have enough stone to request."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_default_rate_is_four_for_one(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 4}
    )
    supply_gold_before = game.resource_supply[teyuna_core.ResourceCard.GOLD]
    supply_stone_before = game.resource_supply[teyuna_core.ResourceCard.STONE]

    action = teyuna_core.TradeWithSupplyAction(
        by=player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.offers is teyuna_core.ResourceCard.GOLD
    assert result.requests is teyuna_core.ResourceCard.STONE
    assert result.rate == 4
    assert game.players[player].resources == collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 0, teyuna_core.ResourceCard.STONE: 1}
    )
    assert game.resource_supply[teyuna_core.ResourceCard.GOLD] == supply_gold_before + 4
    assert (
        game.resource_supply[teyuna_core.ResourceCard.STONE] == supply_stone_before - 1
    )


@pytest.mark.parametrize(
    "location", [k for k, v in teyuna_core.HARBOUR_LOCATIONS.items() if v is None]
)
def test_discounted_rate_if_player_has_generic_harbour(
    location: teyuna_core.Coordinate, game: entities.Game
) -> None:
    game.players[game.active_player].settlements[location] = (
        teyuna_core.SettlementType.TERRACE
    )
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 3}
    )
    action = teyuna_core.TradeWithSupplyAction(
        by=game.active_player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error is None
    assert result.offers is teyuna_core.ResourceCard.GOLD
    assert result.requests is teyuna_core.ResourceCard.STONE
    assert result.rate == 3
    assert game.players[game.active_player].resources == collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 0, teyuna_core.ResourceCard.STONE: 1}
    )


@pytest.mark.parametrize(
    "location,resource",
    [(k, v) for k, v in teyuna_core.HARBOUR_LOCATIONS.items() if v is not None],
)
def test_discounted_rate_if_player_has_specific_harbour(
    location: teyuna_core.Coordinate,
    resource: teyuna_core.ResourceCard,
    game: entities.Game,
) -> None:
    game.players[game.active_player].settlements[location] = (
        teyuna_core.SettlementType.TERRACE
    )
    requests = (
        teyuna_core.ResourceCard.GOLD
        if resource is teyuna_core.ResourceCard.STONE
        else teyuna_core.ResourceCard.STONE
    )
    game.players[game.active_player].resources = collections.Counter({resource: 2})
    action = teyuna_core.TradeWithSupplyAction(
        by=game.active_player,
        offers=resource,
        requests=requests,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error is None
    assert result.offers is resource
    assert result.requests is requests
    assert result.rate == 2
    assert game.players[game.active_player].resources == collections.Counter(
        {resource: 0, requests: 1}
    )


def test_specific_harbour_does_not_apply_to_other_resources(
    game: entities.Game,
) -> None:
    wood_harbour = next(
        location
        for location, resource in teyuna_core.HARBOUR_LOCATIONS.items()
        if resource is teyuna_core.ResourceCard.WOOD
    )
    player = game.active_player
    game.players[player].settlements[wood_harbour] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 3}
    )

    action = teyuna_core.TradeWithSupplyAction(
        by=player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "You do not have enough gold to offer."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_custom_harbour_applies_and_default_does_not(
    game: entities.Game,
) -> None:
    custom_vertex = teyuna_core.canonical_vertex(0, 0, 0)
    other_vertex = teyuna_core.canonical_vertex(0, 0, 1)
    default_wood = next(
        location
        for location, resource in teyuna_core.HARBOUR_LOCATIONS.items()
        if resource is teyuna_core.ResourceCard.WOOD
    )
    game.harbours = (
        teyuna_core.HarbourPair(
            resource=teyuna_core.ResourceCard.GOLD,
            vertices=(custom_vertex, other_vertex),
        ),
    )

    player = game.active_player
    game.players[player].settlements[custom_vertex] = teyuna_core.SettlementType.TERRACE
    game.players[player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )
    action = teyuna_core.TradeWithSupplyAction(
        by=player,
        offers=teyuna_core.ResourceCard.GOLD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(game, action)
    assert result.error is None
    assert result.rate == 2

    # Default wood harbour is no longer on this game.
    game.players[player].settlements = entities.SettlementsCollection(
        _locations={default_wood: teyuna_core.SettlementType.TERRACE}
    )
    game.players[player].resources = collections.Counter(
        {teyuna_core.ResourceCard.WOOD: 2}
    )
    action = teyuna_core.TradeWithSupplyAction(
        by=player,
        offers=teyuna_core.ResourceCard.WOOD,
        requests=teyuna_core.ResourceCard.STONE,
    )
    result = actions.handle_trade_with_supply(game, action)
    assert result.error == "You do not have enough wood to offer."
    assert result.rate == -1
