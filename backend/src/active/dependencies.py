import functools
import random
import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import player, settings
from . import ports, repository as repository_module, services, actions, locks


@functools.cache
def get_repository() -> repository_module.InMemoryActiveGameRepository:
    return repository_module.InMemoryActiveGameRepository()


@functools.cache
def get_game_locks() -> locks.GameLockManager:
    return locks.GameLockManager()


@functools.cache
def get_actions_registry() -> actions.ActionsRegistry:
    settings_ = settings.get_settings()
    reg = actions.ActionsRegistry()
    reg.register(actions.GamePhaseName.FIRST_PLACEMENT)(actions.handle_first_placement)
    reg.register(actions.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
    reg.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_dice_roll)
    reg.register(actions.GamePhaseName.DICE_ROLL)(actions.handle_play_wisdom_card)
    reg.register(actions.GamePhaseName.DISCARD_RESOURCES)(
        actions.handle_discard_resources
    )
    reg.register(actions.GamePhaseName.DICE_PLAY_WARRIOR)(
        actions.handle_dice_play_warrior
    )
    reg.register(actions.GamePhaseName.DICE_PLAY_MAMO)(actions.handle_dice_play_mamo)
    reg.register(actions.GamePhaseName.DICE_PLAY_BLESSED)(
        actions.handle_dice_play_blessed
    )
    reg.register(actions.GamePhaseName.DICE_PLAY_PATHFINDER)(
        actions.handle_dice_play_pathfinder
    )
    reg.register(actions.GamePhaseName.MOVE_CONQUISTATOR)(
        actions.handle_move_conquistator
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(actions.handle_build_terrace)
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(actions.handle_build_path)
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(actions.handle_buy_wisdom_card)
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(actions.handle_propose_trade)
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(actions.handle_accept_trade)
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_with_supply
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_end_trade_and_build
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD)(
        actions.handle_trade_and_build_play_wisdom_card
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)(
        actions.handle_move_conquistator
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO)(
        actions.handle_trade_and_build_play_mamo
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED)(
        actions.handle_trade_and_build_play_blessed
    )
    reg.register(actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER)(
        actions.handle_trade_and_build_play_pathfinder
    )

    timeouts = (
        (
            actions.GamePhaseName.FIRST_PLACEMENT,
            settings_.first_placement_timeout,
            actions.timeouts.timeout_first_placement,
        ),
        (
            actions.GamePhaseName.SECOND_PLACEMENT,
            settings_.second_placement_timeout,
            actions.timeouts.timeout_second_placement,
        ),
        (
            actions.GamePhaseName.DICE_ROLL,
            settings_.dice_roll_timeout,
            actions.timeouts.timeout_dice_roll,
        ),
        (
            actions.GamePhaseName.DISCARD_RESOURCES,
            settings_.discard_resources_timeout,
            actions.timeouts.timeout_discard_resources,
        ),
        (
            actions.GamePhaseName.MOVE_CONQUISTATOR,
            settings_.move_conquistator_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            actions.GamePhaseName.DICE_PLAY_WARRIOR,
            settings_.dice_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
            settings_.trade_and_build_play_warrior_timeout,
            actions.timeouts.timeout_move_conquistator,
        ),
        (
            actions.GamePhaseName.DICE_PLAY_MAMO,
            settings_.dice_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
            settings_.trade_and_build_play_mamo_timeout,
            actions.timeouts.timeout_play_mamo,
        ),
        (
            actions.GamePhaseName.DICE_PLAY_BLESSED,
            settings_.dice_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
            settings_.trade_and_build_play_blessed_timeout,
            actions.timeouts.timeout_play_blessed,
        ),
        (
            actions.GamePhaseName.DICE_PLAY_PATHFINDER,
            settings_.dice_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
            settings_.trade_and_build_play_pathfinder_timeout,
            actions.timeouts.timeout_play_pathfinder,
        ),
        (
            actions.GamePhaseName.TRADE_AND_BUILD,
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
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(get_repository),
    ],
) -> ports.ActiveGame:
    try:
        game = services.retrieve_game(game_id, repository=repository)
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return game


def get_player(
    auth: Annotated[
        player.PlayerAuthenticationService, fastapi.Depends(player.service)
    ],
    session_token: Annotated[str | None, fastapi.Cookie(alias="session-token")] = None,
) -> player.Nickname:
    if session_token is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )

    nickname = auth.retrieve(session_token)
    if nickname is None:
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="player not found"
        )

    return nickname


@functools.cache
def random_generator() -> random.Random:
    return random.Random()
