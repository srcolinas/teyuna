import uuid
from typing import Annotated, cast

import fastapi
import pydantic
from fastapi import status

from . import _dependencies, _entities, _ports, _repository
from ._services import _retrieve

router = fastapi.APIRouter(prefix="/active-games")


@router.get("/{game_id}")
def get_game(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> _ports.ActiveGame:
    return _get_active_game_or_raise(id=game_id, repository=repository)


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> list[_entities.Hex]:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    return game.map


# --- Players ---


@router.get("/{game_id}/players")
def list_players(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> list[_ports.Player]:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    return game.players


class JoinGameRequest(pydantic.BaseModel):
    username: str


@router.get("/{game_id}/players/{username}")
def get_player(
    game_id: uuid.UUID,
    username: str,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> _ports.Player:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    for p in game.players:
        if p.username == username:
            return p
    raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> list[_ports.PlayedSettlement]:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> _ports.PlayedSettlement | None:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    for s in game.settlements:
        if (
            s.location.hex_coord.q == q
            and s.location.hex_coord.r == r
            and s.location.direction == direction
        ):
            return s
    return None


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths")
def list_paths(
    game_id: uuid.UUID,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> list[_ports.PlayedStonePath]:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    repository: Annotated[
        _repository.InMemoryActiveGameRepository,
        fastapi.Depends(_dependencies.get_repository),
    ],
) -> _ports.PlayedStonePath | None:
    game = _get_active_game_or_raise(id=game_id, repository=repository)
    for p in game.paths:
        if (
            p.location.hex_coord.q == q
            and p.location.hex_coord.r == r
            and p.location.direction == direction
        ):
            return p
    return None


def _get_active_game_or_raise(
    *, id: uuid.UUID, repository: _repository.InMemoryActiveGameRepository
) -> _ports.ActiveGame:
    game = _retrieve.retrieve_game(
        id, repository=cast(_retrieve.RetrieveGameRepository, repository)
    )
    if game is None:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return game
