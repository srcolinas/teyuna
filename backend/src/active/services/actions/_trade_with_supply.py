import collections
from typing import Final

from .... import player
from ... import entities
from . import _errors


def trade(
    game: entities.ActiveGame,
    *,
    by: player.Nickname,
    offers: entities.ResourceCard,
    requests: entities.ResourceCard,
) -> None:
    rate = _trade_rate(game, by, offers)
    if game.players[by].resources[offers] < rate:
        raise _errors.InsufficientResources(
            f"You do not have enough {offers.value} to offer."
        )
    if game.resource_supply[requests] < 1:
        raise _errors.InsufficientResources(
            f"The supply does not have enough {requests.value} to request."
        )

    offered = collections.Counter({offers: rate})
    requested = collections.Counter({requests: 1})
    game.players[by].resources -= offered
    game.resource_supply += offered
    game.players[by].resources += requested
    game.resource_supply -= requested


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


_DEFAULT_TRADE_RATE: Final[int] = 4
_GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
_SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
