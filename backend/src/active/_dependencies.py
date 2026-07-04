import functools
from typing import Annotated

import fastapi

from . import _repository
from ._services import _manager


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
