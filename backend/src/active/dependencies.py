import functools
import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import player
from . import ports, repository as repository_module, services, actions


@functools.cache
def get_repository() -> repository_module.InMemoryActiveGameRepository:
    return repository_module.InMemoryActiveGameRepository()


@functools.cache
def get_actions_registry() -> actions.ActionsRegistry:
    reg = actions.ActionsRegistry()
    reg.register(actions.GamePhaseName.FIRST_PLACEMENT)(actions.handle_first_placement)
    reg.register(actions.GamePhaseName.SECOND_PLACEMENT)(
        actions.handle_second_placement
    )
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
