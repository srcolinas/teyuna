import uuid

from ... import player
from .. import entities
from . import _errors, _helpers


def accept_trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    id: uuid.UUID,
) -> None:
    if by != game.turn_order[0]:
        raise _errors.PlayerNotInTurn

    if game.turn_phase is not entities.TurnPhase.TRADE:
        raise _errors.InvalidTurnPhase(
            "Trade proposals can only be accepted in the trade phase."
        )

    if game.phase is not entities.GamePhase.MAIN:
        raise _errors.InvalidGamePhase(
            "Trade proposals can only be accepted in the main phase."
        )

    if id not in game.trade_proposals:
        raise _errors.TradeProposalNotFound(f"Trade proposal {id} not found.")

    proposal = game.trade_proposals[id]
    for resource, amount in proposal.request.items():
        if game.players[by].resources[resource] < amount:
            raise _errors.InsufficientResources(
                f"You do not have enough {resource.value} to accept the trade."
            )

    _helpers.grant_resources(game, by, resources=proposal.offer)
    _helpers.grant_resources(game, proposal.by, resources=proposal.request)
    _helpers.discount_resources(game, proposal.by, resources=proposal.offer)
    _helpers.discount_resources(game, by, resources=proposal.request)
    del game.trade_proposals[id]
