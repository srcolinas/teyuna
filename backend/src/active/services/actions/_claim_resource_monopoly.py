from __future__ import annotations

import collections
import random

from .... import player
from ... import entities

_RND: random.Random = random.Random()

_RESOURCE_TYPES: tuple[entities.ResourceCard, ...] = tuple(entities.ResourceCard)


def claim_resource_monopoly(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    resource: entities.ResourceCard,
) -> entities.ResourceCount:
    taken: entities.ResourceCount = collections.Counter()
    active = game.players[by]
    for nickname, opponent in game.players.items():
        if nickname == by:
            continue
        amount = opponent.resources[resource]
        if amount <= 0:
            continue
        transfer = collections.Counter({resource: amount})
        opponent.resources -= transfer
        active.resources += transfer
        taken += transfer
    return taken


def claim_resource_monopoly_randomly(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    rnd: random.Random = _RND,
) -> entities.ResourceCount:
    resource = rnd.choice(_RESOURCE_TYPES)
    return claim_resource_monopoly(game, by, resource=resource)
