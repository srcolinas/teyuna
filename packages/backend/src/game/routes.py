import random
import uuid
from typing import Annotated, AsyncIterable

import fastapi
import pydantic
from fastapi import status, sse


import teyuna_core

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
    payload: teyuna_core.CreateGameRequest,
    repository_: Annotated[
        repository_module.InMemoryGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    settings_: Annotated[settings.Settings, fastapi.Depends(settings.get_settings)],
) -> teyuna_core.Game:
    return services.create_game(
        params=payload,
        repository=repository_,
        lobby_timeout=settings_.lobby_timeout,
    )


class JoinGameRequest(pydantic.BaseModel):
    nickname: player.Nickname


@router.post("/{game_id}/players")
def join_game(
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
) -> teyuna_core.JoinGameResponse:
    result, token = services.add_player(
        game_id=game_id,
        nickname=payload.nickname,
        repository=repository_,
        auth=auth,
        first_placement_timeout=settings_.first_placement_timeout,
    )
    return teyuna_core.JoinGameResponse(game=result, token=token)


@router.get("/{game_id}")
def get_game(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_core.Game:
    return game


@router.get("/{game_id}/map")
def get_game_map(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[teyuna_core.Hex, ...]:
    return game.map


@router.get("/{game_id}/turn-order")
def get_turn_order(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[player.Nickname, ...]:
    return game.turn_order


@router.get("/{game_id}/conquistator")
def get_conquistator_location(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_core.HexLocation:
    return game.conquistator_location


@router.post("/{game_id}/actions")
async def submit_action(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: teyuna_core.AnyPlayerAction,
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
) -> teyuna_core.AnyActionExecutionResult:
    """Submit a player action for the current game phase.

    Workflow for agents:
    1. Poll `GET /games/{game_id}` (and optionally `GET .../hand`).
    2. If your nickname is in `to_discard_resources`, submit `discard_resources`.
    3. Otherwise act when `turn_order[0]` is you (except trade propose/accept rules).
    4. Choose a payload `kind` that is legal for `phase` — see each action schema.
    5. Use `kind: advance` to roll (`dice roll`), end turn (`trade and build`), or
       apply a random legal move in placement / conquistador / card-resolve phases.
       `advance` is **not** allowed during `discard resources`.

    Illegal or wrong-phase actions return HTTP 400 with a `detail` message.
    The server supplies the authenticated actor and execution RNG separately.
    """
    context = actions.ExecutionContext(
        by=nickname,
        due_to_timeout=False,
        rng=rng,
    )

    result, _ = await services.apply_player_action(
        game_id,
        context,
        payload,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result


@router.get("/{game_id}/players")
def list_players(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_core.Player]:
    return game.players


@router.get("/{game_id}/players/{nickname}")
def get_player(
    nickname: player.Nickname,
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_core.Player:
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
) -> teyuna_core.PlayerHand:
    return services.retrieve_hand(game_id, nickname, repository=repository)


@router.get("/{game_id}/settlements")
def list_settlements(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_core.PlayedSettlement]:
    return game.settlements


@router.get("/{game_id}/settlements/{q}/{r}/{direction}")
def get_settlement(
    q: int,
    r: int,
    direction: int,
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_core.PlayedSettlement | None:
    for s in game.settlements:
        if s.location.q == q and s.location.r == r and s.location.d == direction:
            return s
    return None


@router.get("/{game_id}/paths")
def list_paths(
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> list[teyuna_core.PlayedStonePath]:
    return game.paths


@router.get(
    "/{game_id}/paths/{q}/{r}/{direction}",
)
def get_path(
    q: int,
    r: int,
    direction: int,
    game: Annotated[teyuna_core.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_core.PlayedStonePath | None:
    for p in game.paths:
        if p.location.q == q and p.location.r == r and p.location.d == direction:
            return p
    return None


class SendMessagePayload(pydantic.BaseModel):
    text: str

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/messages")
async def send_message(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: SendMessagePayload,
    broker: Annotated[
        broker_module.EventBroker, fastapi.Depends(dependencies.get_event_broker)
    ],
) -> None:
    await services.send_message(
        game_id,
        nickname,
        payload.text,
        broker=broker,
    )


@router.get("/{game_id}/events", response_class=sse.EventSourceResponse)
async def stream_items(
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    broker: Annotated[
        broker_module.EventBroker, fastapi.Depends(dependencies.get_event_broker)
    ],
) -> AsyncIterable[sse.ServerSentEvent]:
    yield sse.ServerSentEvent(comment="connected")
    async for event in broker.iterate(game_id):
        yield sse.ServerSentEvent(
            data=event.data.model_dump(), event=event.type, id=event.id
        )
