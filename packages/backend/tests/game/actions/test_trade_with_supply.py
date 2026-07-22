import collections

import pytest

from src.game import actions, entities
import teyuna_shared


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    game.players[other].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 4}
    )

    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=other,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_cannot_trade_if_not_enough_resources_from_player(
    game: entities.Game,
) -> None:
    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=game.active_player,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )
    assert result.error == "You do not have enough gold to offer."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_cannot_trade_if_not_enough_resources_from_supply(
    game: entities.Game,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 4}
    )
    game.resource_supply[teyuna_shared.ResourceCard.STONE] = 0
    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=game.active_player,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )
    assert result.error == "The supply does not have enough stone to request."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_default_rate_is_four_for_one(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 4}
    )
    supply_gold_before = game.resource_supply[teyuna_shared.ResourceCard.GOLD]
    supply_stone_before = game.resource_supply[teyuna_shared.ResourceCard.STONE]

    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=player,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.offers is teyuna_shared.ResourceCard.GOLD
    assert result.requests is teyuna_shared.ResourceCard.STONE
    assert result.rate == 4
    assert game.players[player].resources == collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 0, teyuna_shared.ResourceCard.STONE: 1}
    )
    assert (
        game.resource_supply[teyuna_shared.ResourceCard.GOLD] == supply_gold_before + 4
    )
    assert (
        game.resource_supply[teyuna_shared.ResourceCard.STONE]
        == supply_stone_before - 1
    )


@pytest.mark.parametrize(
    "location", [k for k, v in teyuna_shared.HARBOUR_LOCATIONS.items() if v is None]
)
def test_discounted_rate_if_player_has_generic_harbour(
    location: teyuna_shared.Coordinate, game: entities.Game
) -> None:
    game.players[game.active_player].settlements[location] = (
        teyuna_shared.SettlementType.TERRACE
    )
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 3}
    )
    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=game.active_player,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )
    assert result.error is None
    assert result.offers is teyuna_shared.ResourceCard.GOLD
    assert result.requests is teyuna_shared.ResourceCard.STONE
    assert result.rate == 3
    assert game.players[game.active_player].resources == collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 0, teyuna_shared.ResourceCard.STONE: 1}
    )


@pytest.mark.parametrize(
    "location,resource",
    [(k, v) for k, v in teyuna_shared.HARBOUR_LOCATIONS.items() if v is not None],
)
def test_discounted_rate_if_player_has_specific_harbour(
    location: teyuna_shared.Coordinate,
    resource: teyuna_shared.ResourceCard,
    game: entities.Game,
) -> None:
    game.players[game.active_player].settlements[location] = (
        teyuna_shared.SettlementType.TERRACE
    )
    requests = (
        teyuna_shared.ResourceCard.GOLD
        if resource is teyuna_shared.ResourceCard.STONE
        else teyuna_shared.ResourceCard.STONE
    )
    game.players[game.active_player].resources = collections.Counter({resource: 2})
    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=game.active_player,
            offers=resource,
            requests=requests,
        ),
    )
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
        for location, resource in teyuna_shared.HARBOUR_LOCATIONS.items()
        if resource is teyuna_shared.ResourceCard.WOOD
    )
    player = game.active_player
    game.players[player].settlements[wood_harbour] = (
        teyuna_shared.SettlementType.TERRACE
    )
    game.players[player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 3}
    )

    result = actions.handle_trade_with_supply(
        game,
        teyuna_shared.TradeWithSupplyAction(
            by=player,
            offers=teyuna_shared.ResourceCard.GOLD,
            requests=teyuna_shared.ResourceCard.STONE,
        ),
    )
    assert result.error == "You do not have enough gold to offer."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1
