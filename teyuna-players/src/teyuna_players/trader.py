import asyncio
import logging

import httpx

from . import board, entities
from .logging_config import agent_logger_name

_POLL_SECONDS = 2
_PROPOSALS_PER_AGENT = 2
_HARBOURS: dict[board.Coordinate, entities.ResourceCard | None] = {
    board.canonical_vertex(-1, -1, 4): entities.ResourceCard.WOOD,
    board.canonical_vertex(-1, -1, 5): entities.ResourceCard.WOOD,
    board.canonical_vertex(0, -2, 0): None,
    board.canonical_vertex(0, -2, 5): None,
    board.canonical_vertex(1, -2, 0): entities.ResourceCard.MAIZE,
    board.canonical_vertex(1, -2, 1): entities.ResourceCard.MAIZE,
    board.canonical_vertex(2, -1, 0): entities.ResourceCard.STONE,
    board.canonical_vertex(2, -1, 1): entities.ResourceCard.STONE,
    board.canonical_vertex(2, 0, 1): None,
    board.canonical_vertex(2, 0, 2): None,
    board.canonical_vertex(1, 1, 2): entities.ResourceCard.COTTON,
    board.canonical_vertex(1, 1, 3): entities.ResourceCard.COTTON,
    board.canonical_vertex(-1, 2, 2): None,
    board.canonical_vertex(-1, 2, 3): None,
    board.canonical_vertex(-2, 2, 3): None,
    board.canonical_vertex(-2, 2, 4): None,
    board.canonical_vertex(-2, 1, 4): entities.ResourceCard.GOLD,
    board.canonical_vertex(-2, 1, 5): entities.ResourceCard.GOLD,
}


async def build(context: entities.PlayerContext) -> None:
    """Demonstrate legal player-to-player trades, then keep turns moving."""
    logger = logging.getLogger(agent_logger_name(context.nickname))
    proposals_made = 0
    supply_trades_made = 0

    while True:
        try:
            game = await context.client.get_game(context.game_id)
            if game.phase is entities.GamePhaseName.END_GAME:
                return

            if game.phase is entities.GamePhaseName.DISCARD_RESOURCES:
                if await _discard_if_required(context, logger):
                    await asyncio.sleep(_POLL_SECONDS)
                    continue

            if game.phase is entities.GamePhaseName.TRADE_AND_BUILD:
                accepted = await _accept_affordable_proposal(context, logger)
                if accepted:
                    await asyncio.sleep(_POLL_SECONDS)
                    continue

            is_active = bool(game.turn_order and game.turn_order[0] == context.nickname)
            if not is_active:
                await asyncio.sleep(_POLL_SECONDS)
                continue

            if game.phase is entities.GamePhaseName.DICE_ROLL:
                logger.info("%s rolling the dice", context.nickname)
                await context.client.advance_turn()
            elif game.phase in {
                entities.GamePhaseName.FIRST_PLACEMENT,
                entities.GamePhaseName.SECOND_PLACEMENT,
            }:
                terrace, path = _choose_initial_placement(game)
                await context.client.add_initial_placements(
                    terrace=terrace,
                    path=path,
                )
                logger.info(
                    "%s placed a terrace at %s and path at %s",
                    context.nickname,
                    terrace,
                    path,
                )
            elif game.phase is entities.GamePhaseName.TRADE_AND_BUILD:
                proposals = await context.client.list_trade_proposals()
                if any(proposal.by == context.nickname for proposal in proposals):
                    await asyncio.sleep(_POLL_SECONDS)
                    continue

                # A recipient may have accepted between our first game read and
                # the proposal-list read. Refresh the resource snapshot before
                # choosing the next offer.
                game = await context.client.get_game(context.game_id)
                if (
                    game.phase is not entities.GamePhaseName.TRADE_AND_BUILD
                    or not game.turn_order
                    or game.turn_order[0] != context.nickname
                ):
                    continue
                resources = await context.client.get_resources()
                supply_trade = _choose_supply_trade(
                    game,
                    context.nickname,
                    resources,
                )
                if supply_trade is not None and supply_trades_made < 1:
                    offered, requested, rate = supply_trade
                    await context.client.trade_with_supply(
                        offers=offered,
                        requests=requested,
                    )
                    supply_trades_made += 1
                    logger.info(
                        "%s traded %s %s with the supply for 1 %s",
                        context.nickname,
                        rate,
                        offered.value,
                        requested.value,
                    )
                    continue
                targets = {
                    player.nickname
                    for player in game.players
                    if player.nickname != context.nickname
                }
                trade = _choose_trade(resources, targets)
                if trade is not None and proposals_made < _PROPOSALS_PER_AGENT:
                    offered, requested, recipients = trade
                    await context.client.propose_trade(
                        offer={offered: 1},
                        request={requested: 1},
                        to=recipients,
                    )
                    proposals_made += 1
                    logger.info(
                        "%s offered 1 %s for 1 %s to %s (%s/%s proposals)",
                        context.nickname,
                        offered.value,
                        requested.value,
                        sorted(recipients),
                        proposals_made,
                        _PROPOSALS_PER_AGENT,
                    )
                else:
                    logger.info("%s ending trade and build", context.nickname)
                    await context.client.advance_turn()
            else:
                await asyncio.sleep(_POLL_SECONDS)
        except httpx.HTTPError as exc:
            logger.error("%s request failed: %s", context.nickname, exc)
            await asyncio.sleep(_POLL_SECONDS)


async def _discard_if_required(
    context: entities.PlayerContext,
    logger: logging.Logger,
) -> bool:
    resources = await context.client.get_resources()
    required = sum(resources.values()) // 2
    if sum(resources.values()) <= 7:
        return False

    remaining = required
    count: dict[entities.ResourceCard, int] = {}
    for resource, available in resources.items():
        discarded = min(available, remaining)
        if discarded:
            count[resource] = discarded
            remaining -= discarded
        if remaining == 0:
            break
    await context.client.discard_resources(count)
    logger.info(
        "%s discarded %s after a 7 was rolled",
        context.nickname,
        _format_resources(count),
    )
    return True


def _choose_initial_placement(
    game: entities.Game,
) -> tuple[entities.VertexCoordinate, entities.EdgeCoordinate]:
    buildable, free_edges = board.placement_sets(game)
    harbour_vertices = [vertex for vertex in _HARBOURS if vertex in buildable]
    candidates = harbour_vertices + sorted(buildable - set(harbour_vertices))
    for vertex in candidates:
        adjacent = sorted(board.edges_adjacent_to_vertex(*vertex))
        if edge := next((edge for edge in adjacent if edge in free_edges), None):
            return board.to_vertex(vertex), board.to_edge(edge)
    raise RuntimeError("No legal initial terrace and path placement is available")


def _choose_supply_trade(
    game: entities.Game,
    nickname: str,
    resources: dict[entities.ResourceCard, int],
) -> tuple[entities.ResourceCard, entities.ResourceCard, int] | None:
    owned_vertices = {
        board.from_vertex(settlement.location)
        for settlement in game.settlements
        if settlement.owner == nickname
    }
    for offered, available in resources.items():
        rate = 4
        for location, harbour_resource in _HARBOURS.items():
            if location not in owned_vertices:
                continue
            if harbour_resource is None:
                rate = min(rate, 3)
            elif harbour_resource is offered:
                rate = min(rate, 2)
        if available < rate:
            continue
        requested = min(
            (resource for resource in entities.ResourceCard if resource is not offered),
            key=lambda resource: resources.get(resource, 0),
        )
        return offered, requested, rate
    return None


async def _accept_affordable_proposal(
    context: entities.PlayerContext,
    logger: logging.Logger,
) -> bool:
    resources = await context.client.get_resources()
    for proposal in await context.client.list_trade_proposals():
        if context.nickname not in proposal.to:
            continue
        if not all(
            resources.get(card, 0) >= count for card, count in proposal.request.items()
        ):
            continue
        await context.client.accept_trade(proposal.id)
        logger.info(
            "%s accepted %s's trade: %s for %s",
            context.nickname,
            proposal.by,
            _format_resources(proposal.offer),
            _format_resources(proposal.request),
        )
        return True
    return False


def _choose_trade(
    resources: dict[entities.ResourceCard, int],
    targets: set[str],
) -> tuple[entities.ResourceCard, entities.ResourceCard, set[str]] | None:
    if not targets:
        return None
    offered = next((card for card, count in resources.items() if count > 0), None)
    if offered is None:
        return None
    requested = min(
        (resource for resource in entities.ResourceCard if resource is not offered),
        key=lambda resource: resources.get(resource, 0),
    )
    return offered, requested, targets


def _format_resources(resources: dict[entities.ResourceCard, int]) -> str:
    return ", ".join(
        f"{count} {resource.value}" for resource, count in resources.items()
    )
