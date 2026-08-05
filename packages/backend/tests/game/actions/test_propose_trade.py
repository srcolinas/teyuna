import random
import collections

from src.game import actions, entities
import teyuna_core


def test_propose_trade_stores_proposal(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    proposer = game.active_player
    target = game.turn_order[1]
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )
    offer = collections.Counter({teyuna_core.ResourceCard.GOLD: 2})
    request = collections.Counter({teyuna_core.ResourceCard.STONE: 1})

    action = teyuna_core.ProposeTradeAction(
        offer=offer,
        request=request,
        to={target},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert len(game.trade_proposals) == 1
    assert result.proposal_id in game.trade_proposals
    assert result.action.offer == offer
    assert result.action.request == request
    assert result.action.to == {target}
    assert game.trade_proposals[result.proposal_id] == teyuna_core.TradeProposal(
        by=proposer,
        offer=offer,
        request=request,
        to={target},
    )


def test_non_active_player_can_propose_to_active(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    proposer = game.turn_order[1]
    target = game.active_player
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )

    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={target},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id in game.trade_proposals
    proposal = game.trade_proposals[result.proposal_id]
    assert proposal.by == proposer
    assert proposal.to == {target}


def test_non_active_player_can_propose_during_dice_roll(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    proposer = game.turn_order[1]
    target = game.active_player
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )

    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={target},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert game.phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.proposal_id in game.trade_proposals


def test_active_player_cannot_propose_during_dice_roll(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )

    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={game.turn_order[1]},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error == (
        "Active player cannot propose trades during the 'dice roll' phase."
    )
    assert result.proposal_id is None


def test_non_active_player_cannot_propose_to_non_active(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    proposer = game.turn_order[1]
    other = game.turn_order[2]
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )

    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={other},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error == (
        "Non-active players may only propose trades to the active player."
    )
    assert result.proposal_id is None


def test_cannot_propose_if_not_enough_resources(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={game.turn_order[1]},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=game.active_player, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action
    assert result.error == "You do not have enough gold to offer."
    assert result.proposal_id is None


def test_cannot_propose_with_empty_targets(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )
    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to=set(),
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=game.active_player, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action
    assert result.error == "Trade proposal must target at least one player."
    assert result.proposal_id is None


def test_cannot_propose_to_self(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )
    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={proposer},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action
    assert result.error == "Trade proposal cannot target the proposing player."
    assert result.proposal_id is None


def test_cannot_propose_to_unknown_player(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.players[game.active_player].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )
    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={"not-a-player"},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=game.active_player, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action
    assert result.error == "Trade proposal targets unknown player not-a-player."
    assert result.proposal_id is None


def test_propose_does_not_move_resources(game: entities.Game) -> None:
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    proposer = game.active_player
    game.players[proposer].resources = collections.Counter(
        {teyuna_core.ResourceCard.GOLD: 2}
    )

    action = teyuna_core.ProposeTradeAction(
        offer=collections.Counter({teyuna_core.ResourceCard.GOLD: 2}),
        request=collections.Counter({teyuna_core.ResourceCard.STONE: 1}),
        to={game.turn_order[1]},
    )
    result = actions.handle_propose_trade(
        game,
        actions.ExecutionContext(
            by=proposer, due_to_timeout=False, rng=random.Random(0)
        ),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert result.proposal_id in game.trade_proposals
    assert game.players[proposer].resources[teyuna_core.ResourceCard.GOLD] == 2
