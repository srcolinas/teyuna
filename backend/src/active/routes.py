import uuid
from typing import Annotated

import fastapi
import pydantic
from fastapi import status

from .. import player
from . import dependencies, ports, repository as repostory_module, actions, entities

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
) -> tuple[ports.Hex, ...]:
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


# --- Initial placements ---


class InitialPlacementPayload(pydantic.BaseModel):
    terrace: ports.VertexCoordinate
    path: ports.EdgeCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/initial-placements")
def add_initial_placements(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: InitialPlacementPayload,
    repository: Annotated[
        repostory_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
) -> tuple[ports.PlayedSettlement, ports.PlayedStonePath]:
    try:
        game, phase = repository.retrieve(game_id)
    except repostory_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        new_phase = registry.execute(
            phase,
            game,
            actions.FreePlacementAction(
                by=nickname,
                terrace=entities.Coordinate(
                    q=payload.terrace.hex_coord.q,
                    r=payload.terrace.hex_coord.r,
                    d=payload.terrace.direction,
                ),
                path=entities.Coordinate(
                    q=payload.path.hex_coord.q,
                    r=payload.path.hex_coord.r,
                    d=payload.path.direction,
                ),
            ),
        )
    except actions.ActionNotAllowedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.GamePhaseHanlderNotImplementedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
        )
    except actions.PlayerNotInTurnError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except actions.InvalidSettlementLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InvalidPathLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    repository.update(game_id, game, new_phase)
    return ports.PlayedSettlement(
        location=payload.terrace,
        type=entities.SettlementType.TERRACE,
        owner=nickname,
    ), ports.PlayedStonePath(
        location=payload.path,
        owner=nickname,
    )


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
async def build_settlement(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository: Annotated[
        repostory_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
) -> ports.PlayedSettlement:
    raise NotImplementedError


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


@router.post("/{game_id}/settlements/{q}/{r}/{direction}")
def build_path(
    game_id: uuid.UUID,
    q: int,
    r: int,
    direction: int,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository: Annotated[
        repostory_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
) -> ports.PlayedStonePath:
    raise NotImplementedError
