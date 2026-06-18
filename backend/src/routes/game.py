import uuid

import fastapi
from fastapi import status

from .. import entities

router = fastapi.APIRouter(prefix="/games", tags=["games"])


# --- Games ---


@router.post("", status_code=status.HTTP_201_CREATED, response_model=entities.Game)
def create_game(game: entities.Game) -> entities.Game:
    raise NotImplementedError


@router.get("/{game_id}", response_model=entities.Game)
def get_game(game_id: uuid.UUID) -> entities.Game:
    raise NotImplementedError


# --- Players ---


@router.get("/{game_id}/players", response_model=list[entities.Player])
def list_players(game_id: uuid.UUID) -> list[entities.Player]:
    raise NotImplementedError


@router.put("/{game_id}/players", response_model=list[entities.Player])
def add_new_player(game_id: uuid.UUID) -> list[entities.Player]:
    raise NotImplementedError


@router.get("/{game_id}/players/{player_id}", response_model=entities.Player)
def get_player(game_id: uuid.UUID, player_id: uuid.UUID) -> entities.Player:
    raise NotImplementedError


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements", response_model=list[entities.PlayedSettlement])
def list_settlements(game_id: uuid.UUID) -> list[entities.PlayedSettlement]:
    raise NotImplementedError


@router.get(
    "/{game_id}/settlements/{q}/{r}/{direction}",
    response_model=entities.PlayedSettlement,
)
def get_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> entities.PlayedSettlement:
    raise NotImplementedError


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths", response_model=list[entities.PlayedStonePath])
def list_paths(game_id: uuid.UUID) -> list[entities.PlayedStonePath]:
    raise NotImplementedError


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
    response_model=entities.PlayedStonePath,
)
def get_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
) -> entities.PlayedStonePath:
    raise NotImplementedError
