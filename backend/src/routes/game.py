from __future__ import annotations

import functools
import uuid
from typing import Annotated, Any

import fastapi
from fastapi import status

from .. import domain

router = fastapi.APIRouter(prefix="/games", tags=["games"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_description="Game created"
)
def create_game() -> domain.Game:
    raise NotImplementedError("Not implemented")

@router.post("/{id}/join", status_code=status.HTTP_200_OK, response_description="Player joined")
def join_game(id: uuid.UUID, username: str) -> None:
    raise NotImplementedError("Not implemented")

@functools.lru_cache
def _manager() -> _ConnectionManager:
    return _ConnectionManager()

@router.websocket("/{id}/game")
async def game(websocket: fastapi.WebSocket, id: uuid.UUID, manager: Annotated[_ConnectionManager, fastapi.Depends(_manager)]) -> None:
    raise NotImplementedError("Not implemented")

class _ConnectionManager:
    pass