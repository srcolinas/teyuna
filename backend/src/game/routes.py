import uuid

import fastapi
from fastapi import status

from . import _schemas

router = fastapi.APIRouter(prefix="/games", tags=["games"])


# --- Games ---


@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(payload: _schemas.CreateGameRequest) -> _schemas.GameCreated:
    raise NotImplementedError


@router.get("/{game_id}")
def get_game(game_id: uuid.UUID) -> _schemas.ActiveGame:
    raise NotImplementedError


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(game_id: uuid.UUID) -> list[_schemas.Hex]:
    raise NotImplementedError


# --- Players ---


@router.get("/{game_id}/players")
def list_players(game_id: uuid.UUID) -> list[_schemas.Player]:
    raise NotImplementedError


@router.put("/{game_id}/players")
def add_new_player(game_id: uuid.UUID) -> list[_schemas.Player]:
    raise NotImplementedError


@router.get("/{game_id}/players/{player_id}")
def get_player(game_id: uuid.UUID, player_id: uuid.UUID) -> _schemas.Player:
    raise NotImplementedError


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(game_id: uuid.UUID) -> list[_schemas.PlayedSettlement]:
    raise NotImplementedError


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> _schemas.PlayedSettlement:
    raise NotImplementedError


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths")
def list_paths(game_id: uuid.UUID) -> list[_schemas.PlayedStonePath]:
    raise NotImplementedError


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
    response_model=_schemas.PlayedStonePath,
)
def get_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> _schemas.PlayedStonePath:
    raise NotImplementedError
