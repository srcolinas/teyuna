import uuid

from .... import player
from ... import entities
from . import _errors


def propose_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offer: entities.ResourceCount,
    request: entities.ResourceCount,
    to: tuple[player.Nickname, ...],
) -> uuid.UUID:
    if not to:
        raise _errors.InvalidTradeTargets(
            "Trade proposal must target at least one player."
        )

    for resource, amount in offer.items():
        if game.players[by].resources[resource] < amount:
            raise _errors.InsufficientResources(
                f"You do not have enough {resource.value} to offer."
            )

    id = uuid.uuid4()
    game.trade_proposals[id] = entities.TradeProposal(by, offer, request, to)
    return id
