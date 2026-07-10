import uuid

from ... import player
from .. import entities
from . import _errors


def propose_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offer: entities.ResourceCount,
    request: entities.ResourceCount,
) -> uuid.UUID:
    if game.phase is not entities.GamePhase.MAIN:
        raise _errors.InvalidGamePhase(
            "Trade proposals can only be made in the main phase."
        )

    if game.turn_phase is not entities.TurnPhase.TRADE:
        raise _errors.InvalidTurnPhase(
            "Trade proposals can only be made in the trade phase."
        )

    for resource, amount in offer.items():
        if game.players[by].resources[resource] < amount:
            raise _errors.InsufficientResources(
                f"You do not have enough {resource.value} to offer."
            )

    id = uuid.uuid4()
    game.trade_proposals[id] = entities.TradeProposal(by, offer, request)
    return id
