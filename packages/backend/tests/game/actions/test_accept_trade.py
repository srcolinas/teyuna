import collections
import uuid

from src.game import actions, entities
import teyuna_shared


def test_cannot_accept_if_not_in_trade_proposals(game: entities.Game) -> None:
    proposal_id = uuid.uuid4()
    action = teyuna_shared.AcceptTradeAction(by=game.active_player, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Trade proposal {proposal_id} not found."
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()


def test_cannot_accept_if_not_addressed_to_player(game: entities.Game) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[0]
    addressed = game.turn_order[1]
    outsider = game.turn_order[2]
    game.trade_proposals = {
        proposal_id: teyuna_shared.TradeProposal(
            by=proposes,
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 2}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
            to={addressed},
        )
    }

    action = teyuna_shared.AcceptTradeAction(by=outsider, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action
    assert result.error == f"Player {outsider} cannot accept this trade proposal"
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()


def test_cannot_accept_if_not_enough_resources(game: entities.Game) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        proposal_id: teyuna_shared.TradeProposal(
            by=proposes,
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 2}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[proposes].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 2}
    )

    action = teyuna_shared.AcceptTradeAction(by=accepts, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "You do not have enough stone to accept the trade."
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()


def test_cannot_accept_if_proposer_no_longer_has_offer(
    game: entities.Game,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    game.trade_proposals = {
        proposal_id: teyuna_shared.TradeProposal(
            by=proposes,
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 2}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[accepts].resources = collections.Counter(
        {teyuna_shared.ResourceCard.STONE: 1}
    )

    action = teyuna_shared.AcceptTradeAction(by=accepts, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action
    assert result.error == "You do not have enough gold to complete the trade."
    assert result.proposal_id is None
    assert result.proposer == ""
    assert result.acceptor == ""
    assert result.offer == collections.Counter()
    assert result.request == collections.Counter()


def test_accepted_trade_is_removed_from_trade_proposals(
    game: entities.Game,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    action = teyuna_shared.AcceptTradeAction(by=accepts, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({teyuna_shared.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({teyuna_shared.ResourceCard.STONE: 1})
    assert game.trade_proposals == {}


def test_accepted_trade_changes_resources(game: entities.Game) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.turn_order[-1]
    accepts = game.turn_order[0]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    action = teyuna_shared.AcceptTradeAction(by=accepts, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({teyuna_shared.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({teyuna_shared.ResourceCard.STONE: 1})
    assert game.players[proposes].resources[teyuna_shared.ResourceCard.GOLD] == 0
    assert game.players[proposes].resources[teyuna_shared.ResourceCard.STONE] == 1
    assert game.players[accepts].resources[teyuna_shared.ResourceCard.GOLD] == 2
    assert game.players[accepts].resources[teyuna_shared.ResourceCard.STONE] == 0


def test_non_active_player_can_accept_when_addressed(
    game: entities.Game,
) -> None:
    proposal_id = uuid.uuid4()
    proposes = game.active_player
    accepts = game.turn_order[1]
    _seed_successful_trade(game, proposal_id, proposes, accepts)

    action = teyuna_shared.AcceptTradeAction(by=accepts, id=proposal_id)
    result = actions.handle_accept_trade(
        game,
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id == proposal_id
    assert result.proposer == proposes
    assert result.acceptor == accepts
    assert result.offer == collections.Counter({teyuna_shared.ResourceCard.GOLD: 2})
    assert result.request == collections.Counter({teyuna_shared.ResourceCard.STONE: 1})
    assert game.trade_proposals == {}


def _seed_successful_trade(
    game: entities.Game,
    proposal_id: uuid.UUID,
    proposes: str,
    accepts: str,
) -> None:
    game.trade_proposals = {
        proposal_id: teyuna_shared.TradeProposal(
            by=proposes,
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 2}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
            to={accepts},
        )
    }
    game.players[proposes].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 2}
    )
    game.players[accepts].resources = collections.Counter(
        {teyuna_shared.ResourceCard.STONE: 1}
    )
