import uuid
from typing import Annotated

import fastapi
from fastapi import status

from .. import player
from . import dependencies, entities, ports, repository, services

router = fastapi.APIRouter(prefix="/active-games")


@router.get("/{game_id}")
def get_game(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> ports.ActiveGame:
    return game


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> entities.Map:
    return game.map


# --- Players ---


@router.get("/{game_id}/players")
def list_players(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> list[ports.Player]:
    return game.players


@router.get("/{game_id}/players/{nickname}")
def get_player(
    nickname: player.Nickname,
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> ports.Player:
    for p in game.players:
        if p.nickname == nickname:
            return p
    raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# --- Settlements (buildings) ---


@router.get("/{game_id}/settlements")
def list_settlements(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> list[ports.PlayedSettlement]:
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    q: int,
    r: int,
    direction: int,
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> ports.PlayedSettlement | None:
    for s in game.settlements:
        if (
            s.location.hex_coord.q == q
            and s.location.hex_coord.r == r
            and s.location.direction == direction
        ):
            return s
    return None


@router.post("/{game_id}/settlements/{q}/{r}/{direction}")
def buy_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository_: Annotated[
        repository.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
) -> ports.PlayedSettlement:
    game = repository_.retrieve(game_id)
    try:
        if game.phase is entities.GamePhase.INITIAL:
            services.add_initial_terrace(game, nickname, q=q, r=r, direction=direction)
        else:
            services.buy_terrace(game, nickname, q=q, r=r, direction=direction)
    except services.InvalidSettlementLocation:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid settlement location",
        )
    except services.PlayerNotInTurn:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="player not in turn",
        )
    except services.InsufficientResources:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="insufficient resources",
        )
    except services.InvalidGamePhase:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid game phase",
        )
    return ports.PlayedSettlement(
        location=ports.VertexCoordinate(
            hex_coord=ports.HexCoordinate(q=q, r=r), direction=direction
        ),
        type=entities.SettlementType.TERRACE,
        owner=nickname,
    )


# --- Stone paths (buildings) ---


@router.get("/{game_id}/paths")
def list_paths(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> list[ports.PlayedStonePath]:
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    q: int,
    r: int,
    direction: int,
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> ports.PlayedStonePath | None:
    for p in game.paths:
        if (
            p.location.hex_coord.q == q
            and p.location.hex_coord.r == r
            and p.location.direction == direction
        ):
            return p
    return None
