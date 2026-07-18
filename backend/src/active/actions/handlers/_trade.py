import collections
import dataclasses
import uuid
from typing import Final

from .... import player
from ... import entities
from .. import _registry
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
class TradeWithSupplyAction(_registry.PlayerAction):
    offers: entities.ResourceCard
    requests: entities.ResourceCard


def handle_propose_trade(
    game: entities.ActiveGame, action: ProposeTradeAction
) -> _registry.GamePhaseName:
    _validate_trade_targets(game, by=action.by, to=action.to)
    _ensure_resources(
        game.players[action.by].resources,
        action.offer,
        reason="to offer",
    )

    proposal_id = uuid.uuid4()
    game.trade_proposals[proposal_id] = entities.TradeProposal(
        by=action.by,
        offer=collections.Counter(action.offer),
        request=collections.Counter(action.request),
        to=set(action.to),
    )
    return _registry.GamePhaseName.TRADE_AND_BUILD


def handle_accept_trade(
    game: entities.ActiveGame, action: AcceptTradeAction
) -> _registry.GamePhaseName:
    proposal = game.trade_proposals.get(action.id)
    if proposal is None:
        raise _errors.TradeProposalNotFound(f"Trade proposal {action.id} not found.")

    if action.by not in proposal.to:
        raise _errors.TradeNotAddressedToPlayerError(
            f"Player {action.by} cannot accept this trade proposal"
        )

    _ensure_resources(
        game.players[action.by].resources,
        proposal.request,
        reason="to accept the trade",
    )
    _ensure_resources(
        game.players[proposal.by].resources,
        proposal.offer,
        reason="to complete the trade",
    )

    game.take_resources(from_=proposal.by, to=action.by, amount=proposal.offer)
    game.take_resources(from_=action.by, to=proposal.by, amount=proposal.request)
    del game.trade_proposals[action.id]
    return _registry.GamePhaseName.TRADE_AND_BUILD


def handle_trade_with_supply(
    game: entities.ActiveGame, action: TradeWithSupplyAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    rate = _trade_rate(game, action.by, action.offers)
    offered = collections.Counter({action.offers: rate})
    requested = collections.Counter({action.requests: 1})

    _ensure_resources(
        game.players[action.by].resources,
        offered,
        reason="to offer",
    )
    if game.resource_supply[action.requests] < 1:
        raise _errors.InsufficientResourceSupplyError(
            f"The supply does not have enough {action.requests.value} to request."
        )

    game.discard_resources(action.by, offered)
    game.take_from_supply(to=action.by, amount=requested)
    return _registry.GamePhaseName.TRADE_AND_BUILD


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
) -> None:
    if not to:
        raise _errors.InvalidTradeTargets(
            "Trade proposal must target at least one player."
        )
    for target in to:
        if target == by:
            raise _errors.InvalidTradeTargets(
                "Trade proposal cannot target the proposing player."
            )
        if target not in game.players:
            raise _errors.InvalidTradeTargets(
                f"Trade proposal targets unknown player {target}."
            )


def _ensure_resources(
    resources: entities.ResourceCount,
    cost: entities.ResourceCount,
    *,
    reason: str,
) -> None:
    for resource, amount in cost.items():
        if resources[resource] < amount:
            raise _errors.InsufficientResourcesError(
                f"You do not have enough {resource.value} {reason}."
            )


_DEFAULT_TRADE_RATE: Final[int] = 4
_GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
_SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
