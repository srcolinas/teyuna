import functools
import random
import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import settings
from . import player
import teyuna_core

from . import (
    repository as repository_module,
    services,
    actions,
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
    reg.register(teyuna_core.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    reg.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(
        actions.handle_first_placement
    )
    reg.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
    reg.register(teyuna_core.GamePhaseName.SECOND_PLACEMENT)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    reg.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_play_wisdom_card)
    reg.register(teyuna_core.GamePhaseName.DICE_ROLL)(actions.handle_propose_trade)
    reg.register(teyuna_core.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR)(
        actions.handle_dice_play_warrior
    )
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_MAMO)(
        actions.handle_dice_play_mamo
    )
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_MAMO)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_BLESSED)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    reg.register(teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    reg.register(teyuna_core.GamePhaseName.MOVE_CONQUISTATOR)(actions.handle_advance)
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_build_terrace
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(actions.handle_build_path)
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_buy_wisdom_card
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_propose_trade
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(actions.handle_accept_trade)
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_with_supply
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_and_build_play_wisdom_card
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_move_conquistator
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_advance
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_trade_and_build_play_mamo
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_advance
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_trade_and_build_play_blessed
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_advance
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_trade_and_build_play_pathfinder
    )
    reg.register(teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_advance
    )
    reg.register(teyuna_core.GamePhaseName.END_GAME)(actions.handle_end_game)

    timeouts = (
        (
            teyuna_core.GamePhaseName.LOBBY,
            settings_.lobby_timeout,
            actions.timeouts.timeout_lobby,
        ),
        (
            teyuna_core.GamePhaseName.FIRST_PLACEMENT,
            settings_.first_placement_timeout,
            actions.timeouts.timeout_first_placement,
        ),
        (
            teyuna_core.GamePhaseName.SECOND_PLACEMENT,
            settings_.second_placement_timeout,
            actions.timeouts.timeout_second_placement,
        ),
        (
            teyuna_core.GamePhaseName.DICE_ROLL,
            settings_.dice_roll_timeout,
            actions.timeouts.timeout_dice_roll,
        ),
        (
            teyuna_core.GamePhaseName.DISCARD_RESOURCES,
            settings_.discard_resources_timeout,
            actions.timeouts.timeout_discard_resources,
        ),
        (
            teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
            settings_.move_conquistator_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR,
            settings_.dice_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            settings_.trade_and_build_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            teyuna_core.GamePhaseName.DICE_PLAY_MAMO,
            settings_.dice_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
            settings_.trade_and_build_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            teyuna_core.GamePhaseName.DICE_PLAY_BLESSED,
            settings_.dice_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            settings_.trade_and_build_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER,
            settings_.dice_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            settings_.trade_and_build_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            teyuna_core.GamePhaseName.TRADE_AND_BUILD,
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
) -> teyuna_core.Game:
    return services.retrieve_game(game_id, repository=repository)


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
    if game.phase is teyuna_core.GamePhaseName.LOBBY:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game is not active"
        )
    return game_id


def get_player(
    auth: Annotated[
        player.PlayerAuthenticationService, fastapi.Depends(player.service)
    ],
    authorization: Annotated[str | None, fastapi.Header()] = None,
) -> player.Nickname:
    if authorization is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )

    scheme, separator, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not credentials:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid authorization header",
        )

    nickname = auth.retrieve(credentials)
    if nickname is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="player not found"
        )

    return nickname


@functools.cache
def random_generator() -> random.Random:
    return random.Random()


@functools.cache
def get_event_broker() -> broker.EventBroker:
    return broker.EventBroker()
