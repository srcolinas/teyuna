import functools
import uuid
from typing import Annotated

import fastapi
import pydantic
from fastapi import status

from . import entities, ports, repository, services

router = fastapi.APIRouter(prefix="/games", tags=["games"])


@functools.cache
def get_repository() -> repository.InMemoryRepository:
    return repository.InMemoryRepository()


# --- Games ---


@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(
    payload: ports.CreateGameRequest,
    repository: Annotated[
        services.CreateGameRepository, fastapi.Depends(get_repository)
    ],
) -> entities.ProposedGame:
    return services.create_game(params=payload, repository=repository)


@router.get("/{game_id}")
def get_game(game_id: uuid.UUID) -> ports.ActiveGame:
    raise NotImplementedError


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(game_id: uuid.UUID) -> list[entities.Hex]:
    raise NotImplementedError


# --- Players ---


@router.get("/{game_id}/players")
def list_players(game_id: uuid.UUID) -> list[ports.Player]:
    raise NotImplementedError


class JoinGameRequest(pydantic.BaseModel):
    username: str


@router.put("/{game_id}/players")
def join_game(
    game_id: uuid.UUID,
    payload: JoinGameRequest,
    repository: Annotated[
        services.AddPlayerGameRepository, fastapi.Depends(get_repository)
    ],
) -> entities.ProposedGame:
    try:
        game = services.add_player(
            game_id=game_id, username=payload.username, repository=repository
        )
    except services.GameAlreadyFullError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game already full"
        )
    except services.GameExpiredError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game expired"
        )
    return game


@router.get("/{game_id}/players/{player_id}")
def get_player(game_id: uuid.UUID, player_id: uuid.UUID) -> ports.Player:
    raise NotImplementedError


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(game_id: uuid.UUID) -> list[ports.PlayedSettlement]:
    raise NotImplementedError


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> ports.PlayedSettlement:
    raise NotImplementedError


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths")
def list_paths(game_id: uuid.UUID) -> list[ports.PlayedStonePath]:
    raise NotImplementedError


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
    response_model=ports.PlayedStonePath,
)
def get_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> ports.PlayedStonePath:
    raise NotImplementedError
