import collections
import uuid

from src.active import actions, entities


def test_cannot_accept_if_not_in_trade_proposals(game: entities.ActiveGame) -> None:
    proposal_id = uuid.uuid4()
    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=game.active_player, id=proposal_id),
    )
    assert result.succeeded is False
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.TradeProposalNotFound


def test_cannot_accept_if_not_addressed_to_player(game: entities.ActiveGame) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[0]
    addressed = game.turn_order[1]
    outsider = game.turn_order[2]
    game.trade_proposals = {
        proposal_id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={addressed},
        )
    }

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=outsider, id=proposal_id),
    )
    assert result.succeeded is False
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.TradeNotAddressedToPlayerError


def test_cannot_accept_if_not_enough_resources(game: entities.ActiveGame) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        proposal_id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[proposes].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=accepts, id=proposal_id),
    )
    assert result.succeeded is False
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_cannot_accept_if_proposer_no_longer_has_offer(
    game: entities.ActiveGame,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        proposal_id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[accepts].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=accepts, id=proposal_id),
    )
    assert result.succeeded is False
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_accepted_trade_is_removed_from_trade_proposals(
    game: entities.ActiveGame,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=accepts, id=proposal_id),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({entities.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({entities.ResourceCard.STONE: 1})
    assert game.trade_proposals == {}


def test_accepted_trade_changes_resources(game: entities.ActiveGame) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=accepts, id=proposal_id),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({entities.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({entities.ResourceCard.STONE: 1})
    assert game.players[proposes].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[proposes].resources[entities.ResourceCard.STONE] == 1
    assert game.players[accepts].resources[entities.ResourceCard.GOLD] == 2
    assert game.players[accepts].resources[entities.ResourceCard.STONE] == 0


def test_non_active_player_can_accept_when_addressed(
    game: entities.ActiveGame,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.active_player
    accepts = game.turn_order[1]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    result = actions.handle_accept_trade(
        game,
        actions.AcceptTradeAction(by=accepts, id=proposal_id),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({entities.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({entities.ResourceCard.STONE: 1})
    assert game.trade_proposals == {}


def _seed_successful_trade(
    game: entities.ActiveGame,
    proposal_id: uuid.UUID,
    proposes: str,
    accepts: str,
) -> None:
    game.trade_proposals = {
        proposal_id: entities.TradeProposal(
            by=proposes,
            offer=collections.Counter({entities.ResourceCard.GOLD: 2}),
            request=collections.Counter({entities.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[proposes].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 2}
    )
    game.players[accepts].resources = collections.Counter(
        {entities.ResourceCard.STONE: 1}
    )
