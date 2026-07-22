import collections
import functools
import random
import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import settings
from . import player
from . import (
    ports,
    repository as repository_module,
    services,
    actions,
    entities,
    locks,
    broker,
)


@functools.cache
def get_repository() -> repository_module.InMemoryGameRepository:
    return repository_module.InMemoryGameRepository()


@functools.cache
def get_game_locks() -> locks.GameLockManager:
    return locks.GameLockManager()


@functools.cache
def get_actions_registry() -> actions.ActionsRegistry:
    settings_ = settings.get_settings()
    reg = actions.ActionsRegistry()
    reg.register(entities.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    reg.register(entities.GamePhaseName.FIRST_PLACEMENT)(actions.handle_first_placement)
    reg.register(entities.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
    reg.register(entities.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    reg.register(entities.GamePhaseName.DICE_ROLL)(actions.handle_play_wisdom_card)
    reg.register(entities.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    reg.register(entities.GamePhaseName.DICE_PLAY_WARRIOR)(
        actions.handle_dice_play_warrior
    )
    reg.register(entities.GamePhaseName.DICE_PLAY_MAMO)(actions.handle_dice_play_mamo)
    reg.register(entities.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    reg.register(entities.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    reg.register(entities.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(actions.handle_build_terrace)
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(actions.handle_build_path)
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(actions.handle_buy_wisdom_card)
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(actions.handle_propose_trade)
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(actions.handle_accept_trade)
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_with_supply
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_and_build_play_wisdom_card
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_move_conquistator
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_trade_and_build_play_mamo
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_trade_and_build_play_blessed
    )
    reg.register(entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_trade_and_build_play_pathfinder
    )
    reg.register(entities.GamePhaseName.END_GAME)(actions.handle_end_game)

    timeouts = (
        (
            entities.GamePhaseName.LOBBY,
            settings_.lobby_timeout,
            actions.timeouts.timeout_lobby,
        ),
        (
            entities.GamePhaseName.FIRST_PLACEMENT,
            settings_.first_placement_timeout,
            actions.timeouts.timeout_first_placement,
        ),
        (
            entities.GamePhaseName.SECOND_PLACEMENT,
            settings_.second_placement_timeout,
            actions.timeouts.timeout_second_placement,
        ),
        (
            entities.GamePhaseName.DICE_ROLL,
            settings_.dice_roll_timeout,
            actions.timeouts.timeout_dice_roll,
        ),
        (
            entities.GamePhaseName.DISCARD_RESOURCES,
            settings_.discard_resources_timeout,
            actions.timeouts.timeout_discard_resources,
        ),
        (
            entities.GamePhaseName.MOVE_CONQUISTATOR,
            settings_.move_conquistator_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            entities.GamePhaseName.DICE_PLAY_WARRIOR,
            settings_.dice_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            settings_.trade_and_build_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            entities.GamePhaseName.DICE_PLAY_MAMO,
            settings_.dice_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
            settings_.trade_and_build_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            entities.GamePhaseName.DICE_PLAY_BLESSED,
            settings_.dice_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            settings_.trade_and_build_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            entities.GamePhaseName.DICE_PLAY_PATHFINDER,
            settings_.dice_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            settings_.trade_and_build_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            entities.GamePhaseName.TRADE_AND_BUILD,
            settings_.trade_and_build_timeout,
            actions.timeouts.timeout_trade_and_build,
        ),
    )
    for phase, duration, on_timeout in timeouts:
        reg.set_timeout(phase, duration, on_timeout)
    return reg


def get_game(
    game_id: uuid.UUID,
    repository: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(get_repository),
    ],
) -> ports.Game:
    try:
        return services.retrieve_game(game_id, repository=repository)
    except repository_module.GameDoesNotExistError:
        raise


def require_active_game(
    game_id: uuid.UUID,
    repository: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(get_repository),
    ],
) -> uuid.UUID:
    try:
        game = repository.retrieve(game_id)
    except repository_module.GameDoesNotExistError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="game not found"
        )
    if game.phase is entities.GamePhaseName.LOBBY:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game is not active"
        )
    return game_id


def get_player(
    auth: Annotated[
        player.PlayerAuthenticationService, fastapi.Depends(player.service)
    ],
    session_token: Annotated[str | None, fastapi.Cookie(alias="session-token")] = None,
    authorization: Annotated[str | None, fastapi.Header()] = None,
) -> player.Nickname:
    token = session_token
    if authorization is not None:
        scheme, separator, credentials = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not credentials:
            raise fastapi.HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid authorization header",
            )
        token = credentials

    if token is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )

    nickname = auth.retrieve(token)
    if nickname is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="player not found"
        )

    return nickname


@functools.cache
def random_generator() -> random.Random:
    return random.Random()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: collections.defaultdict[
            uuid.UUID, list[fastapi.WebSocket]
        ] = collections.defaultdict(list)

    async def connect(self, game_id: uuid.UUID, websocket: fastapi.WebSocket):
        await websocket.accept()
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: uuid.UUID, websocket: fastapi.WebSocket):
        self.active_connections[game_id].remove(websocket)

    async def broadcast(self, game_id: uuid.UUID, message: str):
        for connection in self.active_connections[game_id]:
            await connection.send_text(message)


@functools.cache
def get_connection_manager() -> ConnectionManager:
    return ConnectionManager()


@functools.cache
def get_event_broker() -> broker.EventBroker:
    return broker.EventBroker()
