import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable, Mapping

import httpx2
import teyuna_core

from . import entities, logging_config, rules

_OFF_TURN_TRADE_PROBABILITY = 0.1
_RNG = random.Random()

Action = Callable[[], Awaitable[None]]


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player focused on trading:
    * Off turn, during dice roll or trade and build, randomly proposes a valid
      1-for-1 trade to the active player when it can afford the offer.
    * On its trade and build turn, randomly proposes a trade, accepts an
      affordable proposal, or skips the turn.
    * Everywhere else, behaves like skipper (empty placement / advance actions).
    * If it needs to discard resources, it does so at random.
    """
    logger = logging.getLogger(logging_config.agent_logger_name(context.nickname))
    logger.info(
        "Trader %s (token: %s) joined game %s",
        context.nickname,
        context.client.token,
        context.client.game_id,
    )
    sleep_time = 2.0
    while True:
        game = await context.client.get_game()
        required = game.to_discard_resources.get(context.nickname)
        if required is not None:
            await _discard(context, logger, required)
            await asyncio.sleep(sleep_time)
            continue

        turn_order = game.turn_order
        is_active = bool(turn_order) and turn_order[0] == context.nickname
        if not is_active:
            if game.phase in (
                teyuna_core.GamePhaseName.TRADE_AND_BUILD,
                teyuna_core.GamePhaseName.DICE_ROLL,
            ):
                await _maybe_propose_off_turn_trade(context, logger, game)
            await asyncio.sleep(sleep_time)
            continue

        match game.phase:
            case (
                teyuna_core.GamePhaseName.FIRST_PLACEMENT
                | teyuna_core.GamePhaseName.SECOND_PLACEMENT
            ):
                logger.info(
                    "%s skipping placement in phase %s",
                    context.nickname,
                    game.phase,
                )
                await context.client.submit_action(teyuna_core.FreePlacementAction())
            case teyuna_core.GamePhaseName.TRADE_AND_BUILD:
                await _trade_and_build(context, logger, game)
            case _:
                logger.info(
                    "%s skipping turn in phase %s",
                    context.nickname,
                    game.phase,
                )
                await context.client.submit_action(teyuna_core.PlayerAction())
        await asyncio.sleep(sleep_time)


async def _discard(
    context: entities.PlayerContext,
    logger: logging.Logger,
    required: int,
) -> None:
    hand = await context.client.get_hand()
    count = rules.pick_discard(hand.resources, required, _RNG)
    result = await context.client.submit_action(
        teyuna_core.DiscardResourcesAction(count=count)
    )
    logger.info(
        "%s discarded %s (next phase %s)",
        context.nickname,
        count,
        result.next_phase,
    )


async def _maybe_propose_off_turn_trade(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_core.Game,
) -> None:
    if not game.turn_order or _RNG.random() >= _OFF_TURN_TRADE_PROBABILITY:
        return
    hand = await context.client.get_hand()
    offer_resource = _random_owned_resource(hand.resources)
    if offer_resource is None:
        return
    request_resource = _RNG.choice(
        [r for r in teyuna_core.ResourceCard if r is not offer_resource]
    )
    active = game.turn_order[0]
    try:
        await context.client.submit_action(
            teyuna_core.ProposeTradeAction(
                offer={offer_resource: 1},
                request={request_resource: 1},
                to={active},
            )
        )
    except httpx2.HTTPStatusError as error:
        # Another concurrent agent may advance the turn after this agent reads
        # the game. A phase-related rejection is expected in that race and
        # must not terminate the entire simulation.
        if error.response.status_code == 400:
            logger.info(
                "%s skipped a stale off-turn trade after the phase changed",
                context.nickname,
            )
            return
        raise
    logger.info(
        "%s proposed off-turn trade to %s: offer %s for %s",
        context.nickname,
        active,
        offer_resource,
        request_resource,
    )


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_core.Game,
) -> None:
    hand = await context.client.get_hand()
    resources = hand.resources
    options: list[Action] = [
        functools.partial(_skip_turn, context, logger),
    ]

    if offer_resource := _random_owned_resource(resources):
        targets = [
            player.nickname
            for player in game.players
            if player.nickname != context.nickname
        ]
        if targets:
            request_resource = _RNG.choice(
                [r for r in teyuna_core.ResourceCard if r is not offer_resource]
            )
            to = set(_RNG.sample(targets, k=_RNG.randint(1, len(targets))))
            options.append(
                functools.partial(
                    _propose_trade,
                    context,
                    logger,
                    offer_resource,
                    request_resource,
                    to,
                )
            )

    acceptable = [
        proposal
        for proposal in game.trade_proposals
        if context.nickname in proposal.to
        and rules.can_afford(resources, proposal.request)
    ]
    if acceptable:
        proposal = _RNG.choice(acceptable)
        options.append(functools.partial(_accept_trade, context, logger, proposal))

    await _RNG.choice(options)()


async def _skip_turn(context: entities.PlayerContext, logger: logging.Logger) -> None:
    logger.info("%s advancing turn (trade and build)", context.nickname)
    await context.client.submit_action(teyuna_core.PlayerAction())


async def _propose_trade(
    context: entities.PlayerContext,
    logger: logging.Logger,
    offer: teyuna_core.ResourceCard,
    request: teyuna_core.ResourceCard,
    to: set[str],
) -> None:
    await context.client.submit_action(
        teyuna_core.ProposeTradeAction(
            offer={offer: 1},
            request={request: 1},
            to=to,
        )
    )
    logger.info(
        "%s proposed trade to %s: offer %s for %s",
        context.nickname,
        to,
        offer,
        request,
    )


async def _accept_trade(
    context: entities.PlayerContext,
    logger: logging.Logger,
    proposal: teyuna_core.ActiveTradeProposal,
) -> None:
    try:
        result = await context.client.submit_action(
            teyuna_core.AcceptTradeAction(id=proposal.id)
        )
    except httpx2.HTTPStatusError as error:
        # Trades and hands can change between selecting a proposal and sending
        # the request because every simulated player runs concurrently. The
        # backend must reject that stale acceptance; the agent should then
        # refresh its state instead of terminating the whole simulation.
        if error.response.status_code == 400:
            logger.info(
                "%s skipped stale trade %s after resources or phase changed",
                context.nickname,
                proposal.id,
            )
            return
        raise
    logger.info(
        "%s accepted trade %s from %s (next phase %s)",
        context.nickname,
        proposal.id,
        proposal.by,
        result.next_phase,
    )


def _random_owned_resource(
    resources: Mapping[teyuna_core.ResourceCard, int],
) -> teyuna_core.ResourceCard | None:
    owned = [resource for resource, amount in resources.items() if amount > 0]
    if not owned:
        return None
    return _RNG.choice(owned)
