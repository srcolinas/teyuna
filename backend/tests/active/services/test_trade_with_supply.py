import collections

import pytest

from src.active import entities, services


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
