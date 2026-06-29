import functools
import uuid
from typing import Annotated, cast

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
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> ports.ActiveGame:
    return _get_active_game_or_raise(id=game_id, repo=repo)


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(
    game_id: uuid.UUID,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> list[entities.Hex]:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    return game.map


# --- Players ---


@router.get("/{game_id}/players")
def list_players(
    game_id: uuid.UUID,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> list[ports.Player]:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    return game.players


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
def get_player(
    game_id: uuid.UUID,
    username: str,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> ports.Player:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    for p in game.players:
        if p.username == username:
            return p
    raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(
    game_id: uuid.UUID,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> list[ports.PlayedSettlement]:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> ports.PlayedSettlement | None:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
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
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> list[ports.PlayedStonePath]:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    repo: Annotated[repository.InMemoryRepository, fastapi.Depends(get_repository)],
) -> ports.PlayedStonePath | None:
    game = _get_active_game_or_raise(id=game_id, repo=repo)
    for p in game.paths:
        if (
            p.location.hex_coord.q == q
            and p.location.hex_coord.r == r
            and p.location.direction == direction
        ):
            return p
    return None


def _get_active_game_or_raise(
    *, id: uuid.UUID, repo: repository.InMemoryRepository
) -> ports.ActiveGame:
    game = services.retrieve_game(
        id, repository=cast(services.RetrieveGameRepository, repo)
    )
    if game is None:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return game
