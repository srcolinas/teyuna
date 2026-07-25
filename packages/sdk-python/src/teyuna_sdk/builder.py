import asyncio
import logging

import teyuna_core

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
    logger.info(
        "Builder %s (token: %s) joined game %s",
        context.nickname,
        context.client.token,
        context.client.game_id,
    )
    sleep_time = 2
    while True:
        game = await context.client.get_game()
        turn_order = game.turn_order
        if not turn_order or turn_order[0] != context.nickname:
            await asyncio.sleep(sleep_time)
            continue

        match game.phase:
            case (
                teyuna_core.GamePhaseName.FIRST_PLACEMENT
                | teyuna_core.GamePhaseName.SECOND_PLACEMENT
            ):
                await _initial_placement(context, logger, game)
            case teyuna_core.GamePhaseName.DICE_ROLL:
                logger.info("%s advancing turn (dice roll)", context.nickname)
                await context.client.submit_action(teyuna_core.PlayerAction())
            case teyuna_core.GamePhaseName.TRADE_AND_BUILD:
                await _trade_and_build(context, logger, sleep_time)
            case _:
                await asyncio.sleep(sleep_time)


async def _initial_placement(
    context: entities.PlayerContext,
    logger: logging.Logger,
    game: teyuna_core.Game,
) -> None:
    vertices = rules.vertices_available_for_free_placement(game)
    preferred = tuple(
        vertex for vertex in vertices if not rules.vertex_touches_desert(game, vertex)
    )
    candidates = preferred or vertices
    if not candidates:
        logger.error("%s found no free placement vertices", context.nickname)
        return

    terrace = candidates[0]
    edges = rules.edges_for_free_placement(game, terrace)
    if not edges:
        logger.error(
            "%s found no free paths for terrace at %s", context.nickname, terrace
        )
        return

    path = edges[0]
    await context.client.submit_action(
        teyuna_core.FreePlacementAction(
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


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
    sleep_time: float,
) -> None:
    while True:
        await asyncio.sleep(sleep_time)
        game = await context.client.get_game()
        if game.phase is not teyuna_core.GamePhaseName.TRADE_AND_BUILD:
            return
        if not game.turn_order or game.turn_order[0] != context.nickname:
            return

        hand = await context.client.get_hand()
        resources = hand.resources

        if terraces := rules.built_terraces(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_core.GREAT_TERRACE_COST):
                terrace = terraces[0]
                await context.client.submit_action(
                    teyuna_core.BuildSettlementAction(
                        item=teyuna_core.SettlementType.GREAT_TERRACE,
                        coordinate=rules.from_vertex(terrace),
                    )
                )
                logger.info("%s built great terrace at %s", context.nickname, terrace)
                continue
        if vertices := rules.vertices_available_for_building(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_core.TERRACE_COST):
                vertex = vertices[0]
                await context.client.submit_action(
                    teyuna_core.BuildSettlementAction(
                        item=teyuna_core.SettlementType.TERRACE,
                        coordinate=rules.from_vertex(vertex),
                    )
                )
                logger.info("%s built terrace at %s", context.nickname, vertex)
                continue
        if edges := rules.edges_available_for_building(game, by=context.nickname):
            if rules.can_afford(resources, teyuna_core.PATH_COST):
                edge = edges[0]
                await context.client.submit_action(
                    teyuna_core.BuildPathAction(coordinate=rules.from_edge(edge))
                )
                logger.info("%s built path at %s", context.nickname, edge)
                continue

        logger.info("%s advancing turn (trade and build)", context.nickname)
        await context.client.submit_action(teyuna_core.PlayerAction())
        return
