import datetime
import random
import uuid

import fastapi
from fastapi import status

from . import _schemas

router = fastapi.APIRouter(prefix="/games", tags=["games"])


# --- Games ---


@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(payload: _schemas.CreateGameRequest) -> _schemas.GameCreated:
    types = (
        [_schemas.HexType.MOUNTAINS] * 3
        + [_schemas.HexType.QUARRIES] * 3
        + [_schemas.HexType.HIGHLANDS] * 4
        + [_schemas.HexType.VALLEYS] * 4
        + [_schemas.HexType.JUNGLE] * 4
        + [_schemas.HexType.DESERT]
    )
    random.shuffle(types)
    numbers = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
    random.shuffle(numbers)

    map = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            try:
                coord = _schemas.HexCoordinate(q=q, r=r)
            except ValueError:
                continue
            type = types.pop()
            if type is _schemas.HexType.DESERT:
                number = 7
            else:
                number = numbers.pop()
            map.append(
                _schemas.Hex(
                    coordinate=coord,
                    type=type,
                    number=number,
                )
            )
    return _schemas.GameCreated(
        id=uuid.uuid4(),
        map=map,
        num_players=payload.num_players,
        expiration=datetime.datetime.now() + datetime.timedelta(seconds=60),
    )


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
