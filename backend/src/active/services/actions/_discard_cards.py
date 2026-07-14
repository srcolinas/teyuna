from __future__ import annotations

import collections
import random

from .... import player
from ... import entities
from . import _errors

_RND: random.Random = random.Random()


def discard_cards(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    resources: entities.ResourceCount,
) -> None:
    hand = game.players[to].resources
    total = sum(hand.values())
    if total <= 7:
        raise _errors.InvalidDiscard("Player does not have enough cards to discard.")
    expected = total // 2
    if sum(resources.values()) != expected:
        raise _errors.InvalidDiscard(
            f"Must discard exactly {expected} cards, got {sum(resources.values())}."
        )
    for resource, amount in resources.items():
        if hand[resource] < amount:
            raise _errors.InsufficientResources

    discarded = collections.Counter(resources)
    game.players[to].resources -= discarded
    game.resource_supply += discarded


def discard_random_half(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    rnd: random.Random = _RND,
) -> None:
    hand = game.players[to].resources
    total = sum(hand.values())
    if total <= 7:
        return
    pool: list[entities.ResourceCard] = []
    for resource, amount in hand.items():
        pool.extend([resource] * amount)
    selected = rnd.sample(pool, total // 2)
    discard_cards(game, to, resources=collections.Counter(selected))
