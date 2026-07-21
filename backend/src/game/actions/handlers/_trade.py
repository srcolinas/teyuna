import collections
import uuid
from typing import Final

import pydantic

from ... import player, entities
from .. import _registry


class ProposeTradeAction(_registry.PlayerAction):
    offer: entities.ResourceCount
    request: entities.ResourceCount
    to: set[player.Nickname]


class AcceptTradeAction(_registry.PlayerAction):
    id: uuid.UUID


class ProposeTradeResult(_registry.ActionExecutionResult):
    proposal_id: uuid.UUID | None = None


class AcceptedTradeResult(_registry.ActionExecutionResult):
    proposal_id: uuid.UUID | None = None
    proposer: player.Nickname = ""
    acceptor: player.Nickname = ""
    offer: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    request: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class TradeWithSupplyAction(_registry.PlayerAction):
    offers: entities.ResourceCard
    requests: entities.ResourceCard


class TradedWithSupplyResult(_registry.ActionExecutionResult):
    offers: entities.ResourceCard | None = None
    requests: entities.ResourceCard | None = None
    rate: int = -1


def handle_propose_trade(
    game: entities.Game, action: ProposeTradeAction
) -> ProposeTradeResult:
    previous_phase = game.phase
    error = _validate_trade_targets(game, by=action.by, to=action.to)
    if error is not None:
        return ProposeTradeResult(
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
        return ProposeTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )

    proposal_id = uuid.uuid4()
    game.trade_proposals[proposal_id] = entities.TradeProposal(
        by=action.by,
        offer=collections.Counter(action.offer),
        request=collections.Counter(action.request),
        to=set(action.to),
    )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return ProposeTradeResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        proposal_id=proposal_id,
    )


def handle_accept_trade(
    game: entities.Game, action: AcceptTradeAction
) -> AcceptedTradeResult:
    previous_phase = game.phase
    proposal = game.trade_proposals.get(action.id)
    if proposal is None:
        return AcceptedTradeResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Trade proposal {action.id} not found.",
        )

    if action.by not in proposal.to:
        return AcceptedTradeResult(
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
        return AcceptedTradeResult(
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
        return AcceptedTradeResult(
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
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return AcceptedTradeResult(
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
    game: entities.Game, action: TradeWithSupplyAction
) -> TradedWithSupplyResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return TradedWithSupplyResult(
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
        return TradedWithSupplyResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=error,
        )
    if game.resource_supply[action.requests] < 1:
        return TradedWithSupplyResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=(
                f"The supply does not have enough {action.requests.value} to request."
            ),
        )

    game.discard_resources(action.by, offered)
    game.take_from_supply(to=action.by, amount=requested)
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    return TradedWithSupplyResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        offers=action.offers,
        requests=action.requests,
        rate=rate,
    )


def _trade_rate(
    game: entities.Game,
    by: player.Nickname,
    offers: entities.ResourceCard,
) -> int:
    rate = _DEFAULT_TRADE_RATE
    settlements = game.players[by].settlements
    for location, harbour_resource in entities.HARBOUR_LOCATIONS.items():
        if location not in settlements:
            continue
        if harbour_resource is None:
            rate = min(rate, _GENERIC_HARBOUR_TRADE_RATE)
        elif harbour_resource == offers:
            rate = min(rate, _SPECIFIC_HARBOUR_TRADE_RATE)
    return rate


def _validate_trade_targets(
    game: entities.Game,
    *,
    by: player.Nickname,
    to: set[player.Nickname],
) -> str | None:
    if not to:
        return "Trade proposal must target at least one player."
    for target in to:
        if target == by:
            return "Trade proposal cannot target the proposing player."
        if target not in game.players:
            return f"Trade proposal targets unknown player {target}."
    return None


def _ensure_resources(
    resources: entities.ResourceCount,
    cost: entities.ResourceCount,
    *,
    reason: str,
) -> str | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return f"You do not have enough {resource.value} {reason}."
    return None


_DEFAULT_TRADE_RATE: Final[int] = 4
_GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
_SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
