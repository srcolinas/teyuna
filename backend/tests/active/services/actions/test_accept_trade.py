import collections
import uuid

import pytest

from src.active import entities
from src.active.services import actions


def test_cannot_accept_if_not_in_trade_proposals(game: entities.ActiveGame) -> None:
    game.trade_proposals = {}
    id = uuid.uuid4()
    with pytest.raises(
        actions.TradeProposalNotFound,
        match=f"Trade proposal {id} not found.",
    ):
        actions.accept_trade(
            game,
            by=game.active_player,
            id=id,
        )


def test_cannot_accept_if_not_enough_resources(game: entities.ActiveGame) -> None:
    id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(accepts,),
        )
    }
    with pytest.raises(
        actions.InsufficientResources,
        match="You do not have enough stone to accept the trade.",
    ):
        actions.accept_trade(
            game,
            by=accepts,
            id=id,
        )


def test_accepted_trade_is_removed_from_trade_proposals(
    game: entities.ActiveGame,
) -> None:
    id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(accepts,),
        )
    }
    game.players[proposes].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[accepts].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
    actions.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.trade_proposals == {}


def test_accepted_trade_changes_proposer_resources(
    game: entities.ActiveGame,
) -> None:
    id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(accepts,),
        )
    }
    game.players[proposes].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[accepts].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
    actions.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.players[proposes].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 0, entities.ResourceCard.STONE: 1}
    )


def test_accepted_trade_changes_acceptor_resources(
    game: entities.ActiveGame,
) -> None:
    id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=(accepts,),
        )
    }
    game.players[proposes].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[accepts].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
    actions.accept_trade(
        game,
        by=accepts,
        id=id,
    )
    assert game.players[accepts].resources == collections.Counter(
        {entities.ResourceCard.GOLD: 2, entities.ResourceCard.STONE: 0}
    )
