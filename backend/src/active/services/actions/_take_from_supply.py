from __future__ import annotations

import collections
import random

from .... import player
from ... import entities
from . import _errors

_RND: random.Random = random.Random()


def take_from_supply(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    resources: entities.ResourceCount,
) -> entities.ResourceCount:
    total = sum(resources.values())
    if total != 2:
        raise _errors.InvalidTakeFromSupply(
            f"Must take exactly 2 resources, got {total}."
        )
    return _grant_from_supply(game, by, resources=resources)


def take_from_supply_randomly(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    rnd: random.Random = _RND,
) -> entities.ResourceCount:
    pool: list[entities.ResourceCard] = []
    for resource, amount in game.resource_supply.items():
        pool.extend([resource] * amount)
    if not pool:
        return collections.Counter()
    selected = rnd.sample(pool, min(2, len(pool)))
    return _grant_from_supply(game, by, resources=collections.Counter(selected))


def _grant_from_supply(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
    *,
    resources: entities.ResourceCount,
) -> entities.ResourceCount:
    for resource, amount in resources.items():
        if game.resource_supply[resource] < amount:
            raise _errors.InsufficientResources

    taken = collections.Counter(resources)
    game.resource_supply -= taken
    game.players[by].resources += taken
    return taken
