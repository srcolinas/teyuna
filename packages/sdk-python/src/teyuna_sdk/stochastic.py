import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable, Mapping

import httpx2
import teyuna_shared

from . import entities, logging_config, rules

_OFF_TURN_TRADE_PROBABILITY = 0.25
_RNG = random.Random()

Action = Callable[[], Awaitable[None]]


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who decide actions to take completely at random:
    * In the first placement first, it will decide whether to build anything or
      let the game decide. If it decides to build, it will build a random terrace
      and a random path next to it. The same is true for the second placement.
    * In the dice roll phase, it will decide whether to
      * Play a random wisdom card.
      * Roll the dice.
    * In the trade and build phase, it will decide among the following actions:
      * Build a great terrace if it can afford it.
      * Build a terrace if it can afford it.
      * Build a path if it can afford it.
      * Buy wisdom card if it can afford it.
      * Skip the turn (even it it can afford the above actions).
      * Propose a trade with to a random number of players. The trade will be with a random resource and
       a random amount.
      * Accept a a random trade proposed by a random player.
      * Trade with the supply. A random amount that is valid.
    * If it needs to move the conquistator, it will move it to a random valid position and
      steal a random resource from a random player in the tile.
    * If it ever needs to discard resources, it will do so at random.
    * It can randomly propose trades to other players if it has the resources to do so.
    """
    logger = logging.getLogger(logging_config.agent_logger_name(context.nickname))
    sleep_time = 2.0
    while True:
        game = await context.client.get_game()
        required = game.to_discard_resources.get(context.nickname)
        if required is not None:
            await _discard(context, logger, required)
            continue

        turn_order = game.turn_order
        is_active = bool(turn_order) and turn_order[0] == context.nickname
        if not is_active:
            if game.phase in (
                teyuna_shared.GamePhaseName.TRADE_AND_BUILD,
                teyuna_shared.GamePhaseName.DICE_ROLL,
            ):
                await _maybe_propose_off_turn_trade(context, logger, game)
            await asyncio.sleep(sleep_time)
            continue

        match game.phase:
            case (
                teyuna_shared.GamePhaseName.FIRST_PLACEMENT
                | teyuna_shared.GamePhaseName.SECOND_PLACEMENT
            ):
                await _initial_placement(context, logger, game)
            case teyuna_shared.GamePhaseName.DICE_ROLL:
                await _dice_roll(context, logger)
            case (
                teyuna_shared.GamePhaseName.MOVE_CONQUISTATOR
                | teyuna_shared.GamePhaseName.DICE_PLAY_WARRIOR
                | teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
            ):
                await _move_conquistator(context, logger, game)
            case teyuna_shared.GamePhaseName.TRADE_AND_BUILD:
                await _trade_and_build(context, logger, game)
            case _:
                pass
        await asyncio.sleep(sleep_time)


async def _discard(
    context: entities.PlayerContext,
    logger: logging.Logger,
    required: int,
) -> None:
    hand = await context.client.get_hand()
    count = rules.pick_discard(hand.resources, required, _RNG)
    result = await context.client.submit_action(
        teyuna_shared.DiscardResourcesAction(count=count)
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
    game: teyuna_shared.Game,
) -> None:
    if not game.turn_order or _RNG.random() >= _OFF_TURN_TRADE_PROBABILITY:
        return
    hand = await context.client.get_hand()
    offer_resource = _random_owned_resource(hand.resources)
    if offer_resource is None:
        return
    request_resource = _RNG.choice(
        [r for r in teyuna_shared.ResourceCard if r is not offer_resource]
    )
    active = game.turn_order[0]
    try:
        await context.client.submit_action(
            teyuna_shared.ProposeTradeAction(
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


async def _initial_placement(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_shared.Game,
) -> None:
    if _RNG.random() < 0.5:
        logger.info("%s skipping initial placement", context.nickname)
        await context.client.submit_action(teyuna_shared.FreePlacementAction())
        return

    vertices = rules.vertices_available_for_free_placement(game)
    if not vertices:
        logger.error("%s found no free placement vertices", context.nickname)
        return
    terrace = _RNG.choice(vertices)
    edges = rules.edges_for_free_placement(game, terrace)
    if not edges:
        logger.error(
            "%s found no free paths for terrace at %s", context.nickname, terrace
        )
        return
    path = _RNG.choice(edges)
    await context.client.submit_action(
        teyuna_shared.FreePlacementAction(
            terrace=rules.from_vertex(terrace),
            path=rules.from_edge(path),
        )
    )
    logger.info(
        "%s placed initial terrace at %s and path at %s",
        context.nickname,
        terrace,
        path,
    )


async def _dice_roll(
    context: entities.PlayerContext,
    logger: logging.Logger,
) -> None:
    hand = await context.client.get_hand()
    if teyuna_shared.WisdomCard.WARRIOR in hand.wisdom_cards and _RNG.random() < 0.5:
        result = await context.client.submit_action(
            teyuna_shared.PlayWisdomCardAction(card=teyuna_shared.WisdomCard.WARRIOR)
        )
        logger.info(
            "%s played warrior (next phase %s)", context.nickname, result.next_phase
        )
        return
    logger.info("%s advancing turn (dice roll)", context.nickname)
    await context.client.submit_action(teyuna_shared.PlayerAction())


async def _move_conquistator(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_shared.Game,
) -> None:
    current = game.conquistator_location
    candidates = [
        tile.coordinate
        for tile in game.map
        if tile.coordinate.q != current.q or tile.coordinate.r != current.r
    ]
    if not candidates:
        logger.error("%s found no conquistator destinations", context.nickname)
        return
    location = _RNG.choice(candidates)
    others = [
        player.nickname
        for player in game.players
        if player.nickname != context.nickname and player.num_resources > 0
    ]
    take_from = _RNG.choice(others) if others and _RNG.random() < 0.5 else None
    await context.client.submit_action(
        teyuna_shared.MoveConquistatorAction(
            q=location.q,
            r=location.r,
            from_player=take_from,
        )
    )
    logger.info(
        "%s moved conquistator to %s (take_from=%s)",
        context.nickname,
        location,
        take_from,
    )


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_shared.Game,
) -> None:
    hand = await context.client.get_hand()
    resources = hand.resources
    options: list[Action] = [
        functools.partial(_skip_turn, context, logger),
    ]

    if terraces := rules.built_terraces(game, by=context.nickname):
        if rules.can_afford(resources, teyuna_shared.GREAT_TERRACE_COST):
            terrace = _RNG.choice(terraces)
            options.append(
                functools.partial(_build_great_terrace, context, logger, terrace)
            )
    if vertices := rules.vertices_available_for_building(game, by=context.nickname):
        if rules.can_afford(resources, teyuna_shared.TERRACE_COST):
            vertex = _RNG.choice(vertices)
            options.append(functools.partial(_build_terrace, context, logger, vertex))
    if edges := rules.edges_available_for_building(game, by=context.nickname):
        if rules.can_afford(resources, teyuna_shared.PATH_COST):
            edge = _RNG.choice(edges)
            options.append(functools.partial(_build_path, context, logger, edge))
    if rules.can_afford(resources, teyuna_shared.WISDOM_CARD_COST):
        options.append(functools.partial(_buy_wisdom, context, logger))

    if offer_resource := _random_owned_resource(resources):
        targets = [
            player.nickname
            for player in game.players
            if player.nickname != context.nickname
        ]
        if targets:
            request_resource = _RNG.choice(
                [r for r in teyuna_shared.ResourceCard if r is not offer_resource]
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

    offerable = [
        resource
        for resource, amount in resources.items()
        if amount >= teyuna_shared.DEFAULT_TRADE_RATE
    ]
    if offerable:
        offers = _RNG.choice(offerable)
        requests = _RNG.choice(
            [r for r in teyuna_shared.ResourceCard if r is not offers]
        )
        options.append(
            functools.partial(_trade_with_supply, context, logger, offers, requests)
        )

    await _RNG.choice(options)()


async def _skip_turn(context: entities.PlayerContext, logger: logging.Logger) -> None:
    logger.info("%s advancing turn (trade and build)", context.nickname)
    await context.client.submit_action(teyuna_shared.PlayerAction())


async def _build_great_terrace(
    context: entities.PlayerContext,
    logger: logging.Logger,
    terrace: teyuna_shared.VertexCoordinate,
) -> None:
    await context.client.submit_action(
        teyuna_shared.BuildSettlementAction(
            item=teyuna_shared.SettlementType.GREAT_TERRACE,
            coordinate=rules.from_vertex(terrace),
        )
    )
    logger.info("%s built great terrace at %s", context.nickname, terrace)


async def _build_terrace(
    context: entities.PlayerContext,
    logger: logging.Logger,
    vertex: teyuna_shared.VertexCoordinate,
) -> None:
    await context.client.submit_action(
        teyuna_shared.BuildSettlementAction(
            item=teyuna_shared.SettlementType.TERRACE,
            coordinate=rules.from_vertex(vertex),
        )
    )
    logger.info("%s built terrace at %s", context.nickname, vertex)


async def _build_path(
    context: entities.PlayerContext,
    logger: logging.Logger,
    edge: teyuna_shared.EdgeCoordinate,
) -> None:
    await context.client.submit_action(
        teyuna_shared.BuildPathAction(coordinate=rules.from_edge(edge))
    )
    logger.info("%s built path at %s", context.nickname, edge)


async def _buy_wisdom(context: entities.PlayerContext, logger: logging.Logger) -> None:
    result = await context.client.submit_action(teyuna_shared.BuyWisdomCardAction())
    logger.info(
        "%s bought wisdom card (next phase %s)", context.nickname, result.next_phase
    )


async def _propose_trade(
    context: entities.PlayerContext,
    logger: logging.Logger,
    offer: teyuna_shared.ResourceCard,
    request: teyuna_shared.ResourceCard,
    to: set[str],
) -> None:
    await context.client.submit_action(
        teyuna_shared.ProposeTradeAction(
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
    proposal: teyuna_shared.ActiveTradeProposal,
) -> None:
    try:
        result = await context.client.submit_action(
            teyuna_shared.AcceptTradeAction(id=proposal.id)
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


async def _trade_with_supply(
    context: entities.PlayerContext,
    logger: logging.Logger,
    offers: teyuna_shared.ResourceCard,
    requests: teyuna_shared.ResourceCard,
) -> None:
    result = await context.client.submit_action(
        teyuna_shared.TradeWithSupplyAction(offers=offers, requests=requests)
    )
    logger.info(
        "%s traded with supply %s for %s (next phase %s)",
        context.nickname,
        offers,
        requests,
        result.next_phase,
    )


def _random_owned_resource(
    resources: Mapping[teyuna_shared.ResourceCard, int],
) -> teyuna_shared.ResourceCard | None:
    owned = [resource for resource, amount in resources.items() if amount > 0]
    if not owned:
        return None
    return _RNG.choice(owned)
