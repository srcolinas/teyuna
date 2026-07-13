import uuid

from .... import player
from ... import entities
from . import _errors


def accept_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    id: uuid.UUID,
) -> None:
    if id not in game.trade_proposals:
        raise _errors.TradeProposalNotFound(f"Trade proposal {id} not found.")

    proposal = game.trade_proposals[id]
    for resource, amount in proposal.request.items():
        if game.players[by].resources[resource] < amount:
            raise _errors.InsufficientResources(
                f"You do not have enough {resource.value} to accept the trade."
            )

    game.players[by].resources -= proposal.request
    game.players[by].resources += proposal.offer
    game.players[proposal.by].resources -= proposal.offer
    game.players[proposal.by].resources += proposal.request
    del game.trade_proposals[id]
