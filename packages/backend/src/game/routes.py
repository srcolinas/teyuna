import collections
import random
import uuid
from typing import Annotated, AsyncIterable, cast

import fastapi
import pydantic
from fastapi import status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from starlette import websockets

from . import player
from .. import settings
import teyuna_shared

from . import (
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


# --- Games ---


@router.get("/{game_id}/map")
def get_game_map(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[teyuna_shared.Hex, ...]:
    return game.map


# --- Turn order ---


@router.get("/{game_id}/turn-order")
def get_turn_order(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> tuple[player.Nickname, ...]:
    return game.turn_order


@router.post("/{game_id}/turn-order")
async def advance_or_phase(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
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
) -> tuple[teyuna_shared.GamePhaseName, player.Nickname]:
    result, game = await services.apply_player_action(
        game_id,
        teyuna_shared.PlayerAction(by=nickname, rng_=rng),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase, game.active_player


# --- Conquistator ---


@router.get("/{game_id}/conquistator")
def get_conquistator_location(
    game: Annotated[teyuna_shared.Game, fastapi.Depends(dependencies.get_game)],
) -> teyuna_shared.HexCoordinate:
    return game.conquistator_location


class MoveConquistatorPayload(pydantic.BaseModel):
    location: teyuna_shared.HexCoordinate
    take_from: player.Nickname | None = None

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/conquistator")
async def move_conquistator(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: MoveConquistatorPayload,
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
) -> teyuna_shared.HexCoordinate:
    result, game = await services.apply_player_action(
        game_id,
        teyuna_shared.MoveConquistatorAction(
            by=nickname,
            q=payload.location.q,
            r=payload.location.r,
            from_player=payload.take_from,
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return teyuna_shared.HexCoordinate(
        q=game.conquistator_location.q, r=game.conquistator_location.r
    )


# --- Discard ---


class DiscardResourcesPayload(pydantic.BaseModel):
    count: dict[teyuna_shared.ResourceCard, int]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/discard")
async def discard_resources(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: DiscardResourcesPayload,
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
) -> teyuna_shared.GamePhaseName:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.DiscardResourcesAction(
            by=nickname,
            count=collections.Counter(payload.count),
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase


# --- Wisdom cards ---


class PlayWisdomCardPayload(pydantic.BaseModel):
    card: teyuna_shared.WisdomCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards")
async def play_wisdom_card(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: PlayWisdomCardPayload,
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
) -> teyuna_shared.GamePhaseName:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.PlayWisdomCardAction(by=nickname, card=payload.card),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase


@router.post("/{game_id}/wisdom-cards/buy")
async def buy_wisdom_card(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
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
) -> teyuna_shared.GamePhaseName:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.BuyWisdomCardAction(by=nickname),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase


# --- Trades ---


class ProposeTradePayload(pydantic.BaseModel):
    offer: dict[teyuna_shared.ResourceCard, int]
    request: dict[teyuna_shared.ResourceCard, int]
    to: set[player.Nickname]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/trades")
async def propose_trade(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: ProposeTradePayload,
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
) -> None:
    result, game = await services.apply_player_action(
        game_id,
        teyuna_shared.ProposeTradeAction(
            by=nickname,
            offer=collections.Counter(payload.offer),
            request=collections.Counter(payload.request),
            to=set(payload.to),
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )

    http.raise_if_failed(result)


@router.post("/{game_id}/trades/{proposal_id}/accept")
async def accept_trade(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    proposal_id: uuid.UUID,
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
) -> teyuna_shared.GamePhaseName:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.AcceptTradeAction(by=nickname, id=proposal_id),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase


class TradeWithSupplyPayload(pydantic.BaseModel):
    offers: teyuna_shared.ResourceCard
    requests: teyuna_shared.ResourceCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/trades/supply")
async def trade_with_supply(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: TradeWithSupplyPayload,
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
) -> teyuna_shared.GamePhaseName:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.TradeWithSupplyAction(
            by=nickname,
            offers=payload.offers,
            requests=payload.requests,
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return result.next_phase


# --- Wisdom card resolutions ---


class PlayMamoPayload(pydantic.BaseModel):
    resource: teyuna_shared.ResourceCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/mamo")
async def play_mamo(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: PlayMamoPayload,
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
) -> dict[teyuna_shared.ResourceCard, int]:
    result, game = await services.apply_player_action(
        game_id,
        teyuna_shared.PlayMamoAction(by=nickname, resource=payload.resource),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return dict(game.players[nickname].resources)


class PlayBlessingPayload(pydantic.BaseModel):
    resources: tuple[teyuna_shared.ResourceCard, teyuna_shared.ResourceCard]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/blessing")
async def play_blessing(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: PlayBlessingPayload,
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
) -> dict[teyuna_shared.ResourceCard, int]:
    result, game = await services.apply_player_action(
        game_id,
        teyuna_shared.PlayBlessedAction(by=nickname, resources=payload.resources),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    http.raise_if_failed(result)
    return dict(game.players[nickname].resources)


class PlayPathfinderPayload(pydantic.BaseModel):
    paths: Annotated[
        list[teyuna_shared.EdgeCoordinate],
        pydantic.Field(min_length=1, max_length=2),
    ]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/pathfinder")
async def play_pathfinder(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: PlayPathfinderPayload,
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
) -> list[teyuna_shared.PlayedStonePath]:
    action = teyuna_shared.PlayPathfinderAction(
        by=nickname,
        paths=tuple(
            teyuna_shared.Coordinate(
                q=path.hex_coord.q,
                r=path.hex_coord.r,
                d=path.direction,
            )
            for path in payload.paths
        ),
    )
    result, game = await services.apply_player_action(
        game_id,
        action,
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )

    http.raise_if_failed(result)

    return [
        teyuna_shared.PlayedStonePath(
            owner=nickname,
            location=teyuna_shared.EdgeCoordinate(
                hex_coord=teyuna_shared.HexCoordinate(q=coord.q, r=coord.r),
                direction=coord.d,
            ),
        )
        for coord in action.paths
        if coord in game.players[nickname].paths
    ]


# --- Players ---


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


# --- Initial placements ---


class InitialPlacementPayload(pydantic.BaseModel):
    terrace: teyuna_shared.VertexCoordinate | None = None
    path: teyuna_shared.EdgeCoordinate | None = None

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/initial-placements")
async def add_initial_placements(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
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
    payload: InitialPlacementPayload = InitialPlacementPayload(),
) -> tuple[teyuna_shared.PlayedSettlement, teyuna_shared.PlayedStonePath]:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.FreePlacementAction(
            by=nickname,
            terrace=payload.terrace
            if payload.terrace is None
            else teyuna_shared.Coordinate(
                q=payload.terrace.hex_coord.q,
                r=payload.terrace.hex_coord.r,
                d=payload.terrace.direction,
            ),
            path=payload.path
            if payload.path is None
            else teyuna_shared.Coordinate(
                q=payload.path.hex_coord.q,
                r=payload.path.hex_coord.r,
                d=payload.path.direction,
            ),
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )
    result = cast(teyuna_shared.PlacedBuildingsResult, result)
    settlement = cast(teyuna_shared.Coordinate, result.settlement)
    path = cast(teyuna_shared.Coordinate, result.path)
    http.raise_if_failed(result)
    return teyuna_shared.PlayedSettlement(
        location=teyuna_shared.VertexCoordinate(
            hex_coord=teyuna_shared.HexCoordinate(q=settlement.q, r=settlement.r),
            direction=settlement.d,
        ),
        type=teyuna_shared.SettlementType.TERRACE,
        owner=nickname,
    ), teyuna_shared.PlayedStonePath(
        location=teyuna_shared.EdgeCoordinate(
            hex_coord=teyuna_shared.HexCoordinate(q=path.q, r=path.r),
            direction=path.d,
        ),
        owner=nickname,
    )


# --- Settlements (buildings) ---


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


class BuildSettlementPayload(pydantic.BaseModel):
    item: teyuna_shared.SettlementType
    location: teyuna_shared.VertexCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/settlements")
async def build_settlement(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: BuildSettlementPayload,
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
) -> teyuna_shared.PlayedSettlement:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.BuildSettlementAction(
            by=nickname,
            item=payload.item,
            coordinate=teyuna_shared.Coordinate(
                q=payload.location.hex_coord.q,
                r=payload.location.hex_coord.r,
                d=payload.location.direction,
            ),
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )

    http.raise_if_failed(result)

    return teyuna_shared.PlayedSettlement(
        owner=nickname,
        location=teyuna_shared.VertexCoordinate(
            hex_coord=teyuna_shared.HexCoordinate(
                q=payload.location.hex_coord.q, r=payload.location.hex_coord.r
            ),
            direction=payload.location.direction,
        ),
        type=payload.item,
    )


# --- Stone paths (buildings) ---


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


class BuildPathPayload(pydantic.BaseModel):
    location: teyuna_shared.EdgeCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/paths")
async def build_path(
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    _active: Annotated[uuid.UUID, fastapi.Depends(dependencies.require_active_game)],
    game_id: uuid.UUID,
    payload: BuildPathPayload,
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
) -> teyuna_shared.PlayedStonePath:
    result, _ = await services.apply_player_action(
        game_id,
        teyuna_shared.BuildPathAction(
            by=nickname,
            coordinate=teyuna_shared.Coordinate(
                q=payload.location.hex_coord.q,
                r=payload.location.hex_coord.r,
                d=payload.location.direction,
            ),
        ),
        repository=repository,
        registry=registry,
        game_locks=game_locks,
        broker=broker,
    )

    http.raise_if_failed(result)

    return teyuna_shared.PlayedStonePath(
        owner=nickname,
        location=teyuna_shared.EdgeCoordinate(
            hex_coord=teyuna_shared.HexCoordinate(
                q=payload.location.hex_coord.q, r=payload.location.hex_coord.r
            ),
            direction=payload.location.direction,
        ),
    )


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
