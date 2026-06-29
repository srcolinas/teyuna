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
def get_game(
    game_id: uuid.UUID,
    repository: Annotated[
        services.RetrieveGameRepository, fastapi.Depends(get_repository)
    ],
) -> ports.ActiveGame:
    game = services.retrieve_game(game_id, repository=repository)
    if game is None:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return game


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
    repository_: Annotated[
        services.AddPlayerGameRepository, fastapi.Depends(get_repository)
    ],
) -> entities.ProposedGame:
    try:
        game = services.add_player(
            game_id=game_id, username=payload.username, repository=repository_
        )
    except services.GameAlreadyFullError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game already full"
        )
    except services.GameExpiredError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game expired"
        )
    except repository.GameDoesNotExistError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="game doesn't exist"
        )
    return game


@router.get("/{game_id}/players/{username}")
def get_player(game_id: uuid.UUID, username: str) -> ports.Player:
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
) -> ports.PlayedSettlement | None:
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
