import collections

import pytest

from src.active import actions, entities


def test_propose_trade_stores_proposal(game: entities.ActiveGame) -> None:
    proposer = game.active_player
    target = game.turn_order[1]
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    offer = collections.Counter({entities.ResourceCard.GOLD: 2})
    request = collections.Counter({entities.ResourceCard.STONE: 1})

    phase = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=offer,
            request=request,
            to={target},
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert len(game.trade_proposals) == 1
    proposal_id = next(iter(game.trade_proposals))
    assert game.trade_proposals[proposal_id] == entities.TradeProposal(
        by=proposer,
        offer=offer,
        request=request,
        to={target},
    )


def test_non_active_player_can_propose(game: entities.ActiveGame) -> None:
    proposer = game.turn_order[1]
    target = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )

    phase = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={target},
        ),
    )

    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    proposal = next(iter(game.trade_proposals.values()))
    assert proposal.by == proposer
    assert proposal.to == {target}


def test_cannot_propose_if_not_enough_resources(game: entities.ActiveGame) -> None:
    with pytest.raises(
        actions.InsufficientResourcesError,
        match="You do not have enough gold to offer.",
    ):
        actions.handle_propose_trade(
            game,
            actions.ProposeTradeAction(
                by=game.active_player,
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to={game.turn_order[1]},
            ),
        )


def test_cannot_propose_with_empty_targets(game: entities.ActiveGame) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    with pytest.raises(
        actions.InvalidTradeTargets,
        match="Trade proposal must target at least one player.",
    ):
        actions.handle_propose_trade(
            game,
            actions.ProposeTradeAction(
                by=game.active_player,
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to=set(),
            ),
        )


def test_cannot_propose_to_self(game: entities.ActiveGame) -> None:
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    with pytest.raises(
        actions.InvalidTradeTargets,
        match="Trade proposal cannot target the proposing player.",
    ):
        actions.handle_propose_trade(
            game,
            actions.ProposeTradeAction(
                by=proposer,
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to={proposer},
            ),
        )


def test_cannot_propose_to_unknown_player(game: entities.ActiveGame) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    with pytest.raises(
        actions.InvalidTradeTargets,
        match="Trade proposal targets unknown player",
    ):
        actions.handle_propose_trade(
            game,
            actions.ProposeTradeAction(
                by=game.active_player,
                offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
                request=collections.Counter({entities.ResourceCard.STONE: 1}),
                to={"not-a-player"},
            ),
        )


def test_propose_does_not_move_resources(game: entities.ActiveGame) -> None:
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )

    actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={game.turn_order[1]},
        ),
    )

    assert game.players[proposer].resources[entities.ResourceCard.GOLD] == 2
