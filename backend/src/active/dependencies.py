import functools
import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import player
from . import ports, services


@functools.cache
def get_game_manager() -> services.GameManager:
    return services.GameManager(nodes={})


def get_game(
    game_id: uuid.UUID,
    manager: Annotated[services.GameManager, fastapi.Depends(get_game_manager)],
) -> ports.ActiveGame:
    try:
        game = manager.retrieve(game_id)
    except services.ActiveGameDoesNotExistError:
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
