import collections

import pytest

from src.game import actions, entities


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    game.players[other].resources = collections.Counter({entities.ResourceCard.GOLD: 4})

    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
            by=other,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
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
        actions.TradeWithSupplyAction(
            by=game.active_player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
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
        {entities.ResourceCard.GOLD: 4}
    )
    game.resource_supply[entities.ResourceCard.STONE] = 0
    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
            by=game.active_player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
    )
    assert result.error == "The supply does not have enough stone to request."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1


def test_default_rate_is_four_for_one(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 4}
    )
    supply_gold_before = game.resource_supply[entities.ResourceCard.GOLD]
    supply_stone_before = game.resource_supply[entities.ResourceCard.STONE]

    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
            by=player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.offers is entities.ResourceCard.GOLD
    assert result.requests is entities.ResourceCard.STONE
    assert result.rate == 4
    assert game.players[player].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 0, entities.ResourceCard.STONE: 1}
    )
    assert game.resource_supply[entities.ResourceCard.GOLD] == supply_gold_before + 4
    assert game.resource_supply[entities.ResourceCard.STONE] == supply_stone_before - 1


@pytest.mark.parametrize(
    "location", [k for k, v in entities.HARBOUR_LOCATIONS.items() if v is None]
)
def test_discounted_rate_if_player_has_generic_harbour(
    location: entities.Coordinate, game: entities.Game
) -> None:
    game.players[game.active_player].settlements[location] = (
        entities.SettlementType.TERRACE
    )
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 3}
    )
    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
            by=game.active_player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
    )
    assert result.error is None
    assert result.offers is entities.ResourceCard.GOLD
    assert result.requests is entities.ResourceCard.STONE
    assert result.rate == 3
    assert game.players[game.active_player].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 0, entities.ResourceCard.STONE: 1}
    )


@pytest.mark.parametrize(
    "location,resource",
    [(k, v) for k, v in entities.HARBOUR_LOCATIONS.items() if v is not None],
)
def test_discounted_rate_if_player_has_specific_harbour(
    location: entities.Coordinate,
    resource: entities.ResourceCard,
    game: entities.Game,
) -> None:
    game.players[game.active_player].settlements[location] = (
        entities.SettlementType.TERRACE
    )
    requests = (
        entities.ResourceCard.GOLD
        if resource is entities.ResourceCard.STONE
        else entities.ResourceCard.STONE
    )
    game.players[game.active_player].resources = collections.Counter({resource: 2})
    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
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
        for location, resource in entities.HARBOUR_LOCATIONS.items()
        if resource is entities.ResourceCard.WOOD
    )
    player = game.active_player
    game.players[player].settlements[wood_harbour] = entities.SettlementType.TERRACE
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 3}
    )

    result = actions.handle_trade_with_supply(
        game,
        actions.TradeWithSupplyAction(
            by=player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        ),
    )
    assert result.error == "You do not have enough gold to offer."
    assert result.offers is None
    assert result.requests is None
    assert result.rate == -1
