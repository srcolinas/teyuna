import uuid

from ... import player
from .. import entities
from . import _errors


def accept_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    id: uuid.UUID,
) -> None:
    if by != game.turn_order[0]:
        raise _errors.PlayerNotInTurn

    if id not in game.trade_proposals:
        raise _errors.TradeProposalNotFound(f"Trade proposal {id} not found.")

    proposal = game.trade_proposals[id]
    for resource, amount in proposal.request.items():
        if game.players[by].resources[resource] < amount:
            raise _errors.InsufficientResources(
                f"You do not have enough {resource.value} to accept the trade."
            )

    game.grant_resources(by, resources=proposal.offer)
    game.grant_resources(proposal.by, resources=proposal.request)
    game.discount_resources(proposal.by, resources=proposal.offer)
    game.discount_resources(by, resources=proposal.request)
    game.remove_trade_proposal(id)
