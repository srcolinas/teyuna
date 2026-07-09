import uuid

from ... import player
from .. import entities, services


def propose_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offer: entities.ResourceCount,
    request: entities.ResourceCount,
) -> uuid.UUID:
    for resource, amount in offer.items():
        if game.players[by].resources[resource] < amount:
            raise services.InsufficientResources(
                f"You do not have enough {resource.value} to offer."
            )

    id = game.add_trade_proposal(by, offer=offer, request=request)
    return id
