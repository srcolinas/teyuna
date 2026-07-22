import asyncio
import logging

import httpx2

from . import board, entities
from .logging_config import agent_logger_name

# Cost totals (public API only exposes num_resources, not the hand).
_PATH_RESOURCE_TOTAL = 2
_TERRACE_RESOURCE_TOTAL = 4
_GREAT_TERRACE_RESOURCE_TOTAL = 5


def _player(game: entities.Game, nickname: str) -> entities.Player | None:
    return next((p for p in game.players if p.nickname == nickname), None)


def _can_build_great_terrace(
    game: entities.Game, nickname: str
) -> entities.VertexCoordinate | None:
    player = _player(game, nickname)
    if player is None:
        return None
    if player.available_great_terraces <= 0:
        return None
    if player.num_resources < _GREAT_TERRACE_RESOURCE_TOTAL:
        return None
    for settlement in game.settlements:
        if (
            settlement.owner == nickname
            and settlement.type is entities.SettlementType.TERRACE
        ):
            return settlement.location
    return None


def _can_build_terrace(
    game: entities.Game, nickname: str
) -> entities.VertexCoordinate | None:
    player = _player(game, nickname)
    if player is None:
        return None
    if player.available_terraces <= 0:
        return None
    if player.num_resources < _TERRACE_RESOURCE_TOTAL:
        return None

    buildable, _ = board.placement_sets(game)
    owned_paths = {
        board.from_edge(path.location) for path in game.paths if path.owner == nickname
    }
    for location in buildable:
        adjacent = board.edges_adjacent_to_vertex(location.q, location.r, location.d)
        if adjacent.intersection(owned_paths):
            return board.to_vertex(location)
    return None


def _can_build_path(
    game: entities.Game, nickname: str
) -> entities.EdgeCoordinate | None:
    player = _player(game, nickname)
    if player is None:
        return None
    if player.available_paths <= 0:
        return None
    if player.num_resources < _PATH_RESOURCE_TOTAL:
        return None

    _, free_edges = board.placement_sets(game)
    owned_paths = {
        board.from_edge(path.location) for path in game.paths if path.owner == nickname
    }
    vertices = {
        board.from_vertex(settlement.location)
        for settlement in game.settlements
        if settlement.owner == nickname
    }
    for path in owned_paths:
        vertices.update(board.vertices_of_edge(path))

    for vertex in vertices:
        for edge in board.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d):
            if edge in owned_paths or edge not in free_edges:
                continue
            return board.to_edge(edge)
    return None


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
    logger = logging.getLogger(agent_logger_name(context.nickname))
    sleep_time = 2
    while True:
        try:
            await _tick(context, logger, sleep_time)
        except httpx2.HTTPError as exc:
            logger.error("%s request failed: %s", context.nickname, exc)
            await asyncio.sleep(sleep_time)


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
        case entities.GamePhaseName.DICE_ROLL:
            logger.info("%s advancing turn (dice roll)", context.nickname)
            await context.client.advance_turn()
        case entities.GamePhaseName.TRADE_AND_BUILD:
            await _trade_and_build(context, logger, sleep_time)
        case _:
            await asyncio.sleep(sleep_time)


async def _trade_and_build(
    context: entities.PlayerContext,
    logger: logging.Logger,
    sleep_time: float,
) -> None:
    try_great, try_terrace, try_path = True, True, True
    nickname = context.nickname

    while True:
        await asyncio.sleep(sleep_time)
        game = await context.client.get_game(context.client.game_id)
        if game.phase is not entities.GamePhaseName.TRADE_AND_BUILD:
            return
        if not game.turn_order or game.turn_order[0] != nickname:
            return

        if try_great:
            if location := _can_build_great_terrace(game, nickname):
                try:
                    await context.client.build_settlement(
                        item=entities.SettlementType.GREAT_TERRACE,
                        location=location,
                    )
                    logger.info("%s built great terrace at %s", nickname, location)
                    try_great = try_terrace = try_path = True
                    continue
                except httpx2.HTTPError as exc:
                    logger.error(
                        "%s failed to build great terrace at %s: %s",
                        nickname,
                        location,
                        exc,
                    )
            try_great = False
        elif try_terrace:
            if location := _can_build_terrace(game, nickname):
                try:
                    await context.client.build_settlement(
                        item=entities.SettlementType.TERRACE,
                        location=location,
                    )
                    logger.info("%s built terrace at %s", nickname, location)
                    try_great = try_terrace = try_path = True
                    continue
                except httpx2.HTTPError as exc:
                    logger.error(
                        "%s failed to build terrace at %s: %s",
                        nickname,
                        location,
                        exc,
                    )
            try_terrace = False
        elif try_path:
            if edge := _can_build_path(game, nickname):
                try:
                    await context.client.build_path(edge)
                    logger.info("%s built path at %s", nickname, edge)
                    try_great = try_terrace = try_path = True
                    continue
                except httpx2.HTTPError as exc:
                    logger.error(
                        "%s failed to build path at %s: %s",
                        nickname,
                        edge,
                        exc,
                    )
            try_path = False
        else:
            logger.info("%s advancing turn (trade and build)", nickname)
            await context.client.advance_turn()
            return
