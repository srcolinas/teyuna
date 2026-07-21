import collections

from src.game import actions, entities


def test_propose_trade_stores_proposal(game: entities.Game) -> None:
    proposer = game.active_player
    target = game.turn_order[1]
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    offer = collections.Counter({entities.ResourceCard.GOLD: 2})
    request = collections.Counter({entities.ResourceCard.STONE: 1})

    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=offer,
            request=request,
            to={target},
        ),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert len(game.trade_proposals) == 1
    assert result.proposal_id in game.trade_proposals
    assert game.trade_proposals[result.proposal_id] == entities.TradeProposal(
        by=proposer,
        offer=offer,
        request=request,
        to={target},
    )


def test_non_active_player_can_propose(game: entities.Game) -> None:
    proposer = game.turn_order[1]
    target = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )

    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={target},
        ),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id in game.trade_proposals
    proposal = game.trade_proposals[result.proposal_id]
    assert proposal.by == proposer
    assert proposal.to == {target}


def test_cannot_propose_if_not_enough_resources(game: entities.Game) -> None:
    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={game.turn_order[1]},
        ),
    )
    assert result.error == "You do not have enough gold to offer."
    assert result.proposal_id is None


def test_cannot_propose_with_empty_targets(game: entities.Game) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to=set(),
        ),
    )
    assert result.error == "Trade proposal must target at least one player."
    assert result.proposal_id is None


def test_cannot_propose_to_self(game: entities.Game) -> None:
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={proposer},
        ),
    )
    assert result.error == "Trade proposal cannot target the proposing player."
    assert result.proposal_id is None


def test_cannot_propose_to_unknown_player(game: entities.Game) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=game.active_player,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={"not-a-player"},
        ),
    )
    assert result.error == "Trade proposal targets unknown player not-a-player."
    assert result.proposal_id is None


def test_propose_does_not_move_resources(game: entities.Game) -> None:
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )

    result = actions.handle_propose_trade(
        game,
        actions.ProposeTradeAction(
            by=proposer,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={game.turn_order[1]},
        ),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id in game.trade_proposals
    assert game.players[proposer].resources[entities.ResourceCard.GOLD] == 2
