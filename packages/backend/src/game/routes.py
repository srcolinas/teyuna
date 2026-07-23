import random
import uuid
from typing import Annotated, AsyncIterable

import fastapi
import pydantic
from fastapi import status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from starlette import websockets

import teyuna_shared

from .. import settings


from . import (
    player,
    dependencies,
    http,
    repository as repository_module,
    actions,
    locks,
    services,
    broker as broker_module,
)

router = fastapi.APIRouter(prefix="/games", route_class=http.GameRoute)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_game(
    payload: teyuna_shared.CreateGameRequest,
    repository_: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    settings_: Annotated[settings.Settings, fastapi.Depends(settings.get_settings)],
) -> teyuna_shared.Game:
    return services.create_game(
        params=payload,
        repository=repository_,
        lobby_timeout=settings_.lobby_timeout,
    )


class JoinGameRequest(pydantic.BaseModel):
    nickname: player.Nickname


@router.post("/{game_id}/players")
def join_game(
    response: fastapi.Response,
    game_id: uuid.UUID,
    payload: JoinGameRequest,
    repository_: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    auth: Annotated[
        player.PlayerAuthenticationService, fastapi.Depends(player.service)
    ],
    settings_: Annotated[settings.Settings, fastapi.Depends(settings.get_settings)],
) -> teyuna_shared.Game:
    result, token = services.add_player(
        game_id=game_id,
        nickname=payload.nickname,
        repository=repository_,
        auth=auth,
        first_placement_timeout=settings_.first_placement_timeout,
    )
    response.set_cookie(key="session-token", value=token, httponly=True)
    return result


@router.get("/{game_id}")
def get_game(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.Game:
    return game


@router.get("/{game_id}/map")
def get_game_map(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[teyuna_shared.Hex, ...]:
    return game.map


@router.get("/{game_id}/turn-order")
def get_turn_order(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[player.Nickname, ...]:
    return game.turn_order


@router.get("/{game_id}/conquistator")
def get_conquistator_location(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.HexCoordinate:
    return game.conquistator_location


@router.post("/{game_id}/actions")
async def submit_action(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: teyuna_shared.AnyPlayerAction,
    repository: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
    broker: Annotated[
        broker_module.EventBroker, fastapi.Depends(dependencies.get_event_broker)
    ],
    rng: Annotated[random.Random, fastapi.Depends(dependencies.random_generator)],
) -> teyuna_shared.AnyActionExecutionResult:
    updates: dict[str, object] = {"by": nickname, "due_to_timeout": False}
    if payload.kind == "advance":
        updates["rng_"] = rng
    action = payload.model_copy(update=updates)

    result, _ = await services.apply_player_action(
        game_id,
        action,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result


@router.get("/{game_id}/players")
def list_players(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_shared.Player]:
    return game.players


@router.get("/{game_id}/players/{nickname}")
def get_player(
    nickname: player.Nickname,
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.Player:
    for p in game.players:
        if p.nickname == nickname:
            return p
    raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{game_id}/hand")
def get_hand(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    game_id: uuid.UUID,
    repository: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
) -> teyuna_shared.PlayerHand:
    return services.retrieve_hand(game_id, nickname, repository=repository)


@router.get("/{game_id}/settlements")
def list_settlements(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_shared.PlayedSettlement]:
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    q: int,
    r: int,
    direction: int,
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.PlayedSettlement | None:
    for s in game.settlements:
        if (
            s.location.hex_coord.q == q
            and s.location.hex_coord.r == r
            and s.location.direction == direction
        ):
            return s
    return None


@router.get("/{game_id}/paths")
def list_paths(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_shared.PlayedStonePath]:
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    q: int,
    r: int,
    direction: int,
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.PlayedStonePath | None:
    for p in game.paths:
        if (
            p.location.hex_coord.q == q
            and p.location.hex_coord.r == r
            and p.location.direction == direction
        ):
            return p
    return None


@router.websocket("/{game_id}/chat")
async def chat(
    websocket: fastapi.WebSocket,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    manager: Annotated[
        dependencies.ConnectionManager,
        fastapi.Depends(dependencies.get_connection_manager),
    ],
):
    await manager.connect(game_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(game_id, f"{nickname}: {message}")
    except websockets.WebSocketDisconnect:
        manager.disconnect(game_id, websocket)


@router.get("/{game_id}/events", response_class=EventSourceResponse)
async def stream_items(
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    broker: Annotated[
        broker_module.EventBroker, fastapi.Depends(dependencies.get_event_broker)
    ],
) -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(comment="connected")
    async for event in broker.iterate(game_id):
        yield ServerSentEvent(data=event.data.model_dump(mode="json"), id=str(event.id))
