import collections
from typing import Final

from ... import player
from .. import entities
from . import _errors, _helpers, _map


def trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offers: entities.ResourceCard,
    requests: entities.ResourceCard,
) -> None:
    if by != game.turn_order[0]:
        raise _errors.PlayerNotInTurn
    rate = _trade_rate(game, by, offers)
    if game.players[by].resources[offers] < rate:
        raise _errors.InsufficientResources(
            f"You do not have enough {offers.value} to offer."
        )
    if game.resource_supply[requests] < 1:
        raise _errors.InsufficientResources(
            f"The supply does not have enough {requests.value} to request."
        )

    _helpers.discount_resources(game, by, resources=collections.Counter({offers: rate}))
    _helpers.grant_resources(game, by, resources=collections.Counter({requests: 1}))


def _trade_rate(
    game: entities.ActiveGame,
    by: player.Nickname,
    offers: entities.ResourceCard,
) -> int:
    rate = _DEFAULT_TRADE_RATE
    settlements = game.players[by].settlements
    for location, harbour_resource in _map.HARBOUR_LOCATIONS.items():
        if location not in settlements:
            continue
        if harbour_resource is None:
            rate = min(rate, _GENERIC_HARBOUR_TRADE_RATE)
        elif harbour_resource == offers:
            rate = min(rate, _SPECIFIC_HARBOUR_TRADE_RATE)
    return rate


_DEFAULT_TRADE_RATE: Final[int] = 4
_GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
_SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
