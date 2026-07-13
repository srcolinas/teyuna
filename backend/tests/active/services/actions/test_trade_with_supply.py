import collections

import pytest

from src.active import entities
from src.active.services import actions


def test_cannot_trade_if_not_enough_resources_from_player(
    game: entities.ActiveGame,
) -> None:
    with pytest.raises(
        actions.InsufficientResources, match="You do not have enough gold to offer."
    ):
        actions.trade(
            game,
            by=game.active_player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        )


def test_cannot_trade_if_not_enough_resources_from_supply(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 4}
    )
    game.resource_supply[entities.ResourceCard.STONE] = 0
    with pytest.raises(
        actions.InsufficientResources,
        match="The supply does not have enough stone to request.",
    ):
        actions.trade(
            game,
            by=game.active_player,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        )


@pytest.mark.parametrize(
    "location", [k for k, v in entities.HARBOUR_LOCATIONS.items() if v is None]
)
def test_discounted_rate_if_player_has_generic_harbour(
    location: entities.Coordinate, game: entities.ActiveGame
) -> None:
    game.players[game.active_player].settlements[location] = (
        entities.SettlementType.TERRACE
    )
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 3}
    )
    actions.trade(
        game,
        by=game.active_player,
        offers=entities.ResourceCard.GOLD,
        requests=entities.ResourceCard.STONE,
    )
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
    game: entities.ActiveGame,
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
    actions.trade(
        game,
        by=game.active_player,
        offers=resource,
        requests=requests,
    )
    assert game.players[game.active_player].resources == collections.Counter(
        {resource: 0, requests: 1}
    )
