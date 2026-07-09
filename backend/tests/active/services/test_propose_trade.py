import collections
import uuid

import pytest

from src.active import entities, services


def test_propose_trade_returns_id(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.grant_resources(
        nickname,
        resources=collections.Counter({entities.ResourceCard.GOLD: 2}),
    )
    id = services.propose_trade(
        game,
        by=nickname,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert isinstance(id, uuid.UUID)


def test_cannot_propose_if_not_enough_resources(game: entities.ActiveGame) -> None:
    with pytest.raises(
        services.InsufficientResources, match="You do not have enough gold to offer."
    ):
        services.propose_trade(
            game,
            by=game.turn_order[1],
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )


def test_propose_trade_is_added_to_trade_proposals(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    game.grant_resources(
        nickname,
        resources=collections.Counter({entities.ResourceCard.GOLD: 2}),
    )
    id = services.propose_trade(
        game,
        by=nickname,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert game.trade_proposals == {
        id: entities.TradeProposal(
            by=nickname,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        ),
    }
