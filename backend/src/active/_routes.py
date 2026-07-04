import uuid
from typing import Annotated

import fastapi
import pydantic
from fastapi import status

from .. import player
from . import _dependencies, _entities, _ports
from ._services import _manager

router = fastapi.APIRouter(prefix="/active-games")


@router.get("/{game_id}")
def get_game(
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> _ports.ActiveGame:
    return game


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> list[_entities.Hex]:
    return game.map


# --- Players ---


@router.get("/{game_id}/players")
def list_players(
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> list[_ports.Player]:
    return game.players


class JoinGameRequest(pydantic.BaseModel):
    username: str


@router.get("/{game_id}/players/{username}")
def get_player(
    username: str,
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> _ports.Player:
    for p in game.players:
        if p.username == username:
            return p
    raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> list[_ports.PlayedSettlement]:
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    q: int,
    r: int,
    direction: int,
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> _ports.PlayedSettlement | None:
    for s in game.settlements:
        if (
            s.location.hex_coord.q == q
            and s.location.hex_coord.r == r
            and s.location.direction == direction
        ):
            return s
    return None


@router.post("/{game_id}/settlements/{q}/{r}/{direction}")
def add_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    nickname: Annotated[player.Nickname, fastapi.Depends(_dependencies.get_player)],
    manager: Annotated[
        _manager.GameManager, fastapi.Depends(_dependencies.get_game_manager)
    ],
) -> _ports.PlayedSettlement:
    raise NotImplementedError


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths")
def list_paths(
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> list[_ports.PlayedStonePath]:
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    q: int,
    r: int,
    direction: int,
    game: Annotated[_ports.ActiveGame, fastapi.Depends(_dependencies.get_game)],
) -> _ports.PlayedStonePath | None:
    for p in game.paths:
        if (
            p.location.hex_coord.q == q
            and p.location.hex_coord.r == r
            and p.location.direction == direction
        ):
            return p
    return None
