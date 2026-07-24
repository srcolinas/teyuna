import collections
import uuid

import teyuna_core

from ... import entities


def handle_propose_trade(
    game: entities.Game, action: teyuna_core.ProposeTradeAction
) -> teyuna_core.ProposeTradeResult:
    previous_phase = game.phase
    error = _validate_trade_targets(game, by=action.by, to=action.to)
    if error is not None:
        return teyuna_core.ProposeTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    error = _ensure_resources(
        game.players[action.by].resources,
        action.offer,
        reason="to offer",
    )
    if error is not None:
        return teyuna_core.ProposeTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    proposal_id = uuid.uuid4()
    game.trade_proposals[proposal_id] = teyuna_core.TradeProposal(
        by=action.by,
        offer=collections.Counter(action.offer),
        request=collections.Counter(action.request),
        to=set(action.to),
    )
    return teyuna_core.ProposeTradeResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        proposal_id=proposal_id,
    )


def handle_accept_trade(
    game: entities.Game, action: teyuna_core.AcceptTradeAction
) -> teyuna_core.AcceptedTradeResult:
    previous_phase = game.phase
    proposal = game.trade_proposals.get(action.id)
    if proposal is None:
        return teyuna_core.AcceptedTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Trade proposal {action.id} not found.",
        )

    if action.by not in proposal.to:
        return teyuna_core.AcceptedTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} cannot accept this trade proposal",
        )

    error = _ensure_resources(
        game.players[action.by].resources,
        proposal.request,
        reason="to accept the trade",
    )
    if error is not None:
        return teyuna_core.AcceptedTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    error = _ensure_resources(
        game.players[proposal.by].resources,
        proposal.offer,
        reason="to complete the trade",
    )
    if error is not None:
        return teyuna_core.AcceptedTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    offer = collections.Counter(proposal.offer)
    request = collections.Counter(proposal.request)
    proposer = proposal.by
    game.take_resources(from_=proposal.by, to=action.by, amount=proposal.offer)
    game.take_resources(from_=action.by, to=proposal.by, amount=proposal.request)
    del game.trade_proposals[action.id]
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    return teyuna_core.AcceptedTradeResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        proposal_id=action.id,
        proposer=proposer,
        acceptor=action.by,
        offer=offer,
        request=request,
    )


def handle_trade_with_supply(
    game: entities.Game, action: teyuna_core.TradeWithSupplyAction
) -> teyuna_core.TradedWithSupplyResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_core.TradedWithSupplyResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    rate = _trade_rate(game, action.by, action.offers)
    offered = collections.Counter({action.offers: rate})
    requested = collections.Counter({action.requests: 1})

    error = _ensure_resources(
        game.players[action.by].resources,
        offered,
        reason="to offer",
    )
    if error is not None:
        return teyuna_core.TradedWithSupplyResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    if game.resource_supply[action.requests] < 1:
        return teyuna_core.TradedWithSupplyResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=(
                f"The supply does not have enough {action.requests.value} to request."
            ),
        )

    game.discard_resources(action.by, offered)
    game.take_from_supply(to=action.by, amount=requested)
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    return teyuna_core.TradedWithSupplyResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        offers=action.offers,
        requests=action.requests,
        rate=rate,
    )


def _trade_rate(
    game: entities.Game,
    by: str,
    offers: teyuna_core.ResourceCard,
) -> int:
    rate = teyuna_core.DEFAULT_TRADE_RATE
    settlements = game.players[by].settlements
    for location, harbour_resource in game.harbour_locations.items():
        if location not in settlements:
            continue
        if harbour_resource is None:
            rate = min(rate, teyuna_core.GENERIC_HARBOUR_TRADE_RATE)
        elif harbour_resource == offers:
            rate = min(rate, teyuna_core.SPECIFIC_HARBOUR_TRADE_RATE)
    return rate


def _validate_trade_targets(
    game: entities.Game,
    *,
    by: str,
    to: set[str],
) -> str | None:
    if not to:
        return "Trade proposal must target at least one player."
    for target in to:
        if target == by:
            return "Trade proposal cannot target the proposing player."
        if target not in game.players:
            return f"Trade proposal targets unknown player {target}."
    if by != game.active_player:
        if to != {game.active_player}:
            return "Non-active players may only propose trades to the active player."
    elif game.phase is not teyuna_core.GamePhaseName.TRADE_AND_BUILD:
        return f"Active player cannot propose trades during the '{game.phase.value}' phase."
    return None


def _ensure_resources(
    resources: teyuna_core.ResourceCount,
    cost: teyuna_core.ResourceCount,
    *,
    reason: str,
) -> str | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return f"You do not have enough {resource.value} {reason}."
    return None
