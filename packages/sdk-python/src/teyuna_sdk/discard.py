"""Shared discard helper for sample agents."""

from __future__ import annotations

import logging
import random

import teyuna_core

from . import entities, rules


async def discard_if_required(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_core.Game,
    rng: random.Random,
) -> bool:
    """Discard when ``game.to_discard_resources`` requires it.

    Returns ``True`` if a discard was submitted. Players not listed in
    ``to_discard_resources`` must not attempt to discard (including via a bare
    ``PlayerAction``), even if they are ``turn_order[0]``.
    """
    required = game.to_discard_resources.get(context.nickname)
    if required is None:
        return False

    hand = await context.client.get_hand()
    count = rules.pick_discard(hand.resources, required, rng)
    result = await context.client.submit_action(
        teyuna_core.DiscardResourcesAction(count=count)
    )
    logger.info(
        "%s discarded %s (next phase %s)",
        context.nickname,
        count,
        result.next_phase,
    )
    return True
