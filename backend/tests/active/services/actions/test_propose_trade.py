import collections
import uuid

import pytest

from src.active import entities
from src.active.services import actions


def test_propose_trade_returns_id(game: entities.ActiveGame) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    id = actions.propose_trade(
        game,
        by=game.active_player,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert isinstance(id, uuid.UUID)


def test_cannot_propose_if_not_enough_resources(game: entities.ActiveGame) -> None:
    with pytest.raises(
        actions.InsufficientResources, match="You do not have enough gold to offer."
    ):
        actions.propose_trade(
            game,
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        )


def test_propose_trade_is_added_to_trade_proposals(game: entities.ActiveGame) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    id = actions.propose_trade(
        game,
        by=game.active_player,
        offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
    )
    assert game.trade_proposals == {
        id: entities.TradeProposal(
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
        ),
    }
