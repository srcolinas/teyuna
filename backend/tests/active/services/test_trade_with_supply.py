import collections

import pytest

from src.active import entities, services
from src.active.entities._game import HARBOUR_LOCATIONS


def test_cannot_trade_if_not_in_turn(game: entities.ActiveGame) -> None:
    with pytest.raises(services.PlayerNotInTurn):
        services.trade(
            game,
            by=game.turn_order[1],
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        )


def test_cannot_trade_if_not_enough_resources_from_player(
    game: entities.ActiveGame,
) -> None:
    with pytest.raises(
        services.InsufficientResources, match="You do not have enough gold to offer."
    ):
        services.trade(
            game,
            by=game.turn_order[0],
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        )


def test_cannot_trade_if_not_enough_resources_from_supply(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.grant_resources(
        nickname,
        resources=collections.Counter(
            {entities.ResourceCard.GOLD: 4, entities.ResourceCard.STONE: 19}
        ),
    )
    with pytest.raises(
        services.InsufficientResources,
        match="The supply does not have enough stone to request.",
    ):
        services.trade(
            game,
            by=nickname,
            offers=entities.ResourceCard.GOLD,
            requests=entities.ResourceCard.STONE,
        )


@pytest.mark.parametrize(
    "location", [k for k, v in HARBOUR_LOCATIONS.items() if v is None]
)
def test_discounted_rate_if_player_has_generic_harbour(
    location: entities.Coordinate, game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    game.players[nickname].settlements[location] = entities.SettlementType.TERRACE
    game.grant_resources(
        nickname,
        resources=collections.Counter({entities.ResourceCard.GOLD: 3}),
    )
    services.trade(
        game,
        by=nickname,
        offers=entities.ResourceCard.GOLD,
        requests=entities.ResourceCard.STONE,
    )
    assert game.players[nickname].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 0, entities.ResourceCard.STONE: 1}
    )


@pytest.mark.parametrize(
    "location,resource", [(k, v) for k, v in HARBOUR_LOCATIONS.items() if v is not None]
)
def test_discounted_rate_if_player_has_specific_harbour(
    location: entities.Coordinate,
    resource: entities.ResourceCard,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.players[nickname].settlements[location] = entities.SettlementType.TERRACE
    requests = (
        entities.ResourceCard.GOLD
        if resource is entities.ResourceCard.STONE
        else entities.ResourceCard.STONE
    )
    game.grant_resources(
        nickname,
        resources=collections.Counter({resource: 2}),
    )
    services.trade(
        game,
        by=nickname,
        offers=resource,
        requests=requests,
    )
    assert game.players[nickname].resources == collections.Counter(
        {resource: 0, requests: 1}
    )
