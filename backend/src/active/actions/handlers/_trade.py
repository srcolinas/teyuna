import collections
import dataclasses
import uuid
from typing import Final

from .... import player
from ... import entities
from .. import _registry, _results
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class ProposeTradeAction(_registry.PlayerAction):
    offer: entities.ResourceCount
    request: entities.ResourceCount
    to: set[player.Nickname]


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptTradeAction(_registry.PlayerAction):
    id: uuid.UUID


@dataclasses.dataclass(frozen=True, slots=True)
class ProposeTradeResult(_registry.ActionExecutionResult):
    proposal_id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@dataclasses.dataclass(frozen=True, slots=True)
class TradeWithSupplyAction(_registry.PlayerAction):
    offers: entities.ResourceCard
    requests: entities.ResourceCard


def handle_propose_trade(
    game: entities.ActiveGame, action: ProposeTradeAction
) -> _registry.ActionExecutionResult:
    error = _validate_trade_targets(game, by=action.by, to=action.to)
    if error is not None:
        return _results.fail(error)
    error = _ensure_resources(
        game.players[action.by].resources,
        action.offer,
        reason="to offer",
    )
    if error is not None:
        return _results.fail(error)

    proposal_id = uuid.uuid4()
    game.trade_proposals[proposal_id] = entities.TradeProposal(
        by=action.by,
        offer=collections.Counter(action.offer),
        request=collections.Counter(action.request),
        to=set(action.to),
    )
    return ProposeTradeResult(
        succeeded=True,
        phase=_registry.GamePhaseName.TRADE_AND_BUILD,
        proposal_id=proposal_id,
    )


def handle_accept_trade(
    game: entities.ActiveGame, action: AcceptTradeAction
) -> _registry.ActionExecutionResult:
    proposal = game.trade_proposals.get(action.id)
    if proposal is None:
        return _results.fail(
            _errors.TradeProposalNotFound(f"Trade proposal {action.id} not found.")
        )

    if action.by not in proposal.to:
        return _results.fail(
            _errors.TradeNotAddressedToPlayerError(
                f"Player {action.by} cannot accept this trade proposal"
            )
        )

    error = _ensure_resources(
        game.players[action.by].resources,
        proposal.request,
        reason="to accept the trade",
    )
    if error is not None:
        return _results.fail(error)
    error = _ensure_resources(
        game.players[proposal.by].resources,
        proposal.offer,
        reason="to complete the trade",
    )
    if error is not None:
        return _results.fail(error)

    game.take_resources(from_=proposal.by, to=action.by, amount=proposal.offer)
    game.take_resources(from_=action.by, to=proposal.by, amount=proposal.request)
    del game.trade_proposals[action.id]
    return _results.ok(_registry.GamePhaseName.TRADE_AND_BUILD)


def handle_trade_with_supply(
    game: entities.ActiveGame, action: TradeWithSupplyAction
) -> _registry.ActionExecutionResult:
    if game.active_player != action.by:
        return _results.fail(
            _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")
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
        return _results.fail(error)
    if game.resource_supply[action.requests] < 1:
        return _results.fail(
            _errors.InsufficientResourceSupplyError(
                f"The supply does not have enough {action.requests.value} to request."
            )
        )

    game.discard_resources(action.by, offered)
    game.take_from_supply(to=action.by, amount=requested)
    return _results.ok(_registry.GamePhaseName.TRADE_AND_BUILD)


def _trade_rate(
    game: entities.ActiveGame,
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
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    to: set[player.Nickname],
) -> Exception | None:
    if not to:
        return _errors.InvalidTradeTargets(
            "Trade proposal must target at least one player."
        )
    for target in to:
        if target == by:
            return _errors.InvalidTradeTargets(
                "Trade proposal cannot target the proposing player."
            )
        if target not in game.players:
            return _errors.InvalidTradeTargets(
                f"Trade proposal targets unknown player {target}."
            )
    return None


def _ensure_resources(
    resources: entities.ResourceCount,
    cost: entities.ResourceCount,
    *,
    reason: str,
) -> Exception | None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            return _errors.InsufficientResourcesError(
                f"You do not have enough {resource.value} {reason}."
            )
    return None


_DEFAULT_TRADE_RATE: Final[int] = 4
_GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
_SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
