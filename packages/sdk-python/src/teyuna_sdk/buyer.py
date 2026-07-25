import asyncio
import logging

import teyuna_core

from . import entities, logging_config, rules


async def build(
    context: entities.PlayerContext,
) -> None:
    """
    A player who buys wisdom cards whenever it can afford them and plays
    any held card at the beginning of its turn. Placement and other phases
    are skipped or left to server timeouts.
    """
    logger = logging.getLogger(logging_config.agent_logger_name(context.nickname))
    logger.info(
        "Buyer %s (token: %s) joined game %s",
        context.nickname,
        context.client.token,
        context.client.game_id,
    )
    sleep_time = 2.0
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
                logger.info(
                    "%s skipping placement in phase %s",
                    context.nickname,
                    game.phase,
                )
                await context.client.submit_action(teyuna_core.FreePlacementAction())
            case teyuna_core.GamePhaseName.DICE_ROLL:
                await _dice_roll(context, logger)
            case teyuna_core.GamePhaseName.TRADE_AND_BUILD:
                await _trade_and_build(context, logger)
            case _:
                pass
        await asyncio.sleep(sleep_time)


async def _dice_roll(
    context: entities.PlayerContext,
    logger: logging.Logger,
) -> None:
    hand = await context.client.get_hand()
    if hand.wisdom_cards:
        card = hand.wisdom_cards[0]
        result = await context.client.submit_action(
            teyuna_core.PlayWisdomCardAction(card=card)
        )
        logger.info(
            "%s played %s (next phase %s)",
            context.nickname,
            card,
            result.next_phase,
        )
        return
    logger.info("%s advancing turn (dice roll)", context.nickname)
    await context.client.submit_action(teyuna_core.PlayerAction())


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
) -> None:
    hand = await context.client.get_hand()
    if rules.can_afford(hand.resources, teyuna_core.WISDOM_CARD_COST):
        await _buy_wisdom(context, logger)
        return

    logger.info("%s advancing turn (trade and build)", context.nickname)
    await context.client.submit_action(teyuna_core.PlayerAction())


async def _buy_wisdom(context: entities.PlayerContext, logger: logging.Logger) -> None:
    result = await context.client.submit_action(teyuna_core.BuyWisdomCardAction())
    logger.info(
        "%s bought wisdom card (next phase %s)", context.nickname, result.next_phase
    )
