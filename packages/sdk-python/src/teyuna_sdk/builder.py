import asyncio
import logging

import teyuna_shared

from . import entities, logging_config, rules


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who will build the best possible structures
    given its current resources. This player can win the game
    as building is one of the ways to get points and by
    taking building actions alone a player can reach the
    desired goal of 10 points.
    """
    logger = logging.getLogger(logging_config.agent_logger_name(context.nickname))
    sleep_time = 2
    while True:
        await _tick(context, logger, sleep_time)


async def _tick(
    context: entities.PlayerContext,
    logger: logging.Logger,
    sleep_time: float,
) -> None:
    game = await context.client.get_game(context.client.game_id)
    turn_order = game.turn_order
    if not turn_order or turn_order[0] != context.nickname:
        await asyncio.sleep(sleep_time)
        return

    match game.phase:
        case teyuna_shared.GamePhaseName.DICE_ROLL:
            logger.info("%s advancing turn (dice roll)", context.nickname)
            await context.client.advance_turn()
        case teyuna_shared.GamePhaseName.TRADE_AND_BUILD:
            await _trade_and_build(context, logger, sleep_time)
        case _:
            await asyncio.sleep(sleep_time)


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
    sleep_time: float,
) -> None:
    while True:
        await asyncio.sleep(sleep_time)
        game = await context.client.get_game(context.client.game_id)
        if game.phase is not teyuna_shared.GamePhaseName.TRADE_AND_BUILD:
            return
        if not game.turn_order or game.turn_order[0] != context.nickname:
            return

        hand = await context.client.get_hand()
        resources = hand.resources

        if terraces := rules.built_terraces(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_shared.GREAT_TERRACE_COST):
                terrace = terraces[0]
                await context.client.build_settlement(
                    item=teyuna_shared.SettlementType.GREAT_TERRACE,
                    location=terrace,
                )
                logger.info("%s built great terrace at %s", context.nickname, terrace)
                continue
        if vertices := rules.vertices_available_for_building(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_shared.TERRACE_COST):
                vertex = vertices[0]
                await context.client.build_settlement(
                    item=teyuna_shared.SettlementType.TERRACE,
                    location=vertex,
                )
                logger.info("%s built terrace at %s", context.nickname, vertex)
                continue
        if edges := rules.edges_available_for_building(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_shared.PATH_COST):
                edge = edges[0]
                await context.client.build_path(edge)
                logger.info("%s built path at %s", context.nickname, edge)
                continue

        logger.info("%s advancing turn (trade and build)", context.nickname)
        await context.client.advance_turn()
        return
