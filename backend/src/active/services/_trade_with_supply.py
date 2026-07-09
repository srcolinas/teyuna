import collections

from ... import player
from .. import entities
from . import _errors


def trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offers: entities.ResourceCard,
    requests: entities.ResourceCard,
) -> None:
    if by != game.turn_order[0]:
        raise _errors.PlayerNotInTurn
    if game.players[by].resources[offers] < 4:
        raise _errors.InsufficientResources(
            f"You do not have enough {offers.value} to offer."
        )
    if game.resource_supply[requests] < 1:
        raise _errors.InsufficientResources(
            f"The supply does not have enough {requests.value} to request."
        )

    game.discount_resources(by, resources=collections.Counter({offers: 4}))
    game.grant_resources(by, resources=collections.Counter({requests: 1}))
