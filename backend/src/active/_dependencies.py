import functools
import uuid
from typing import Annotated, cast

import fastapi
from fastapi import status

from .. import player
from . import _ports, _repository
from ._services import _manager, _retrieve


@functools.cache
def get_repository() -> _repository.InMemoryActiveGameRepository:
    return _repository.InMemoryActiveGameRepository()


@functools.cache
def get_game_manager(
    repository: Annotated[
        _manager.ManagedGameRepository, fastapi.Depends(get_repository)
    ],
) -> _manager.GameManager:
    return _manager.GameManager(repository)


def get_game(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(get_repository),
    ],
) -> _ports.ActiveGame:
    try:
        game = _retrieve.retrieve_game(
            game_id, repository=cast(_retrieve.RetrieveGameRepository, repository)
        )
    except _repository.ActiveGameDoesNotExistError:
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
