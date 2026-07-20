import collections
import random
import uuid
from typing import Annotated

import fastapi
import pydantic
from fastapi import status

from .. import player
from . import (
    dependencies,
    ports,
    repository as repository_module,
    actions,
    entities,
    locks,
    services,
)

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


# --- Turn order ---


@router.get("/{game_id}/turn-order")
def get_turn_order(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> tuple[player.Nickname, ...]:
    return game.turn_order


@router.post("/{game_id}/turn-order")
def advance_or_phase(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
    rng: Annotated[random.Random, fastapi.Depends(dependencies.random_generator)],
) -> tuple[actions.GamePhaseName, player.Nickname]:
    try:
        new_phase, game, _ = services.apply_player_action(
            game_id,
            actions.PlayerAction(by=nickname, rng_=rng),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    return new_phase, game.active_player


# --- Conquistator ---


@router.get("/{game_id}/conquistator")
def get_conquistator_location(
    game: Annotated[ports.ActiveGame, fastapi.Depends(dependencies.get_game)],
) -> ports.HexCoordinate:
    return game.conquistator_location


class MoveConquistatorPayload(pydantic.BaseModel):
    location: ports.HexCoordinate
    take_from: player.Nickname | None = None

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/conquistator")
def move_conquistator(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: MoveConquistatorPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> ports.HexCoordinate:
    try:
        _, game, _ = services.apply_player_action(
            game_id,
            actions.MoveConquistatorAction(
                by=nickname,
                q=payload.location.q,
                r=payload.location.r,
                from_player=payload.take_from,
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InvalidConquistatorLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return ports.HexCoordinate(
        q=game.conquistator_location.q, r=game.conquistator_location.r
    )


# --- Wisdom cards ---


class PlayWisdomCardPayload(pydantic.BaseModel):
    card: entities.WisdomCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards")
def play_wisdom_card(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: PlayWisdomCardPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> actions.GamePhaseName:
    try:
        new_phase, _, _ = services.apply_player_action(
            game_id,
            actions.PlayWisdomCardAction(by=nickname, card=payload.card),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.PlayerDoesNotHaveCardError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return new_phase


@router.post("/{game_id}/wisdom-cards/buy")
def buy_wisdom_card(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> actions.GamePhaseName:
    try:
        new_phase, _, _ = services.apply_player_action(
            game_id,
            actions.BuyWisdomCardAction(by=nickname),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.EmptyWisdomDeckError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return new_phase


# --- Trades ---


class ProposeTradePayload(pydantic.BaseModel):
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: set[player.Nickname]

    model_config = pydantic.ConfigDict(frozen=True)


class ProposeTradeResponse(pydantic.BaseModel):
    id: uuid.UUID

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/trades")
def propose_trade(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: ProposeTradePayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> ProposeTradeResponse:
    try:
        _, game, existing_ids = services.apply_player_action(
            game_id,
            actions.ProposeTradeAction(
                by=nickname,
                offer=collections.Counter(payload.offer),
                request=collections.Counter(payload.request),
                to=set(payload.to),
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
            before=lambda g: set(g.trade_proposals),
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except actions.ActionNotAllowedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.GamePhaseHanlderNotImplementedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
        )
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InvalidTradeTargets as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    assert existing_ids is not None
    proposal_id = next(iter(set(game.trade_proposals) - existing_ids))
    return ProposeTradeResponse(id=proposal_id)


@router.post("/{game_id}/trades/{proposal_id}/accept")
def accept_trade(
    game_id: uuid.UUID,
    proposal_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> actions.GamePhaseName:
    try:
        new_phase, _, _ = services.apply_player_action(
            game_id,
            actions.AcceptTradeAction(by=nickname, id=proposal_id),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except actions.ActionNotAllowedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.GamePhaseHanlderNotImplementedError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
        )
    except actions.TradeProposalNotFound as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.TradeNotAddressedToPlayerError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return new_phase


class TradeWithSupplyPayload(pydantic.BaseModel):
    offers: entities.ResourceCard
    requests: entities.ResourceCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/trades/supply")
def trade_with_supply(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: TradeWithSupplyPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> actions.GamePhaseName:
    try:
        new_phase, _, _ = services.apply_player_action(
            game_id,
            actions.TradeWithSupplyAction(
                by=nickname,
                offers=payload.offers,
                requests=payload.requests,
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InsufficientResourceSupplyError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return new_phase


# --- Wisdom card resolutions ---


class PlayMamoPayload(pydantic.BaseModel):
    resource: entities.ResourceCard

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/mamo")
def play_mamo(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: PlayMamoPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> dict[entities.ResourceCard, int]:
    try:
        _, game, _ = services.apply_player_action(
            game_id,
            actions.PlayMamoAction(by=nickname, resource=payload.resource),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    return dict(game.players[nickname].resources)


class PlayBlessingPayload(pydantic.BaseModel):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/blessing")
def play_blessing(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: PlayBlessingPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> dict[entities.ResourceCard, int]:
    try:
        _, game, _ = services.apply_player_action(
            game_id,
            actions.PlayBlessedAction(by=nickname, resources=payload.resources),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InsufficientResourceSupplyError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return dict(game.players[nickname].resources)


class PlayPathfinderPayload(pydantic.BaseModel):
    paths: Annotated[
        list[ports.EdgeCoordinate],
        pydantic.Field(min_length=1, max_length=2),
    ]

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/wisdom-cards/pathfinder")
def play_pathfinder(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: PlayPathfinderPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> list[ports.PlayedStonePath]:
    try:
        _, game, paths_before = services.apply_player_action(
            game_id,
            actions.PlayPathfinderAction(
                by=nickname,
                paths=tuple(
                    entities.Coordinate(
                        q=path.hex_coord.q,
                        r=path.hex_coord.r,
                        d=path.direction,
                    )
                    for path in payload.paths
                ),
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
            before=lambda g: set(g.players[nickname].paths),
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InvalidPathLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    assert paths_before is not None
    placed = game.players[nickname].paths - paths_before
    return [
        ports.PlayedStonePath(
            owner=nickname,
            location=ports.EdgeCoordinate(
                hex_coord=ports.HexCoordinate(q=coord.q, r=coord.r),
                direction=coord.d,
            ),
        )
        for coord in placed
    ]


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
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> tuple[ports.PlayedSettlement, ports.PlayedStonePath]:
    try:
        services.apply_player_action(
            game_id,
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
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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


class BuildSettlementPayload(pydantic.BaseModel):
    item: entities.SettlementType
    location: ports.VertexCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/settlements")
def build_settlement(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: BuildSettlementPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> ports.PlayedSettlement:
    try:
        services.apply_player_action(
            game_id,
            actions.BuildSettlementAction(
                by=nickname,
                item=payload.item,
                coordinate=entities.Coordinate(
                    q=payload.location.hex_coord.q,
                    r=payload.location.hex_coord.r,
                    d=payload.location.direction,
                ),
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InvalidSettlementLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return ports.PlayedSettlement(
        owner=nickname,
        location=ports.VertexCoordinate(
            hex_coord=ports.HexCoordinate(
                q=payload.location.hex_coord.q, r=payload.location.hex_coord.r
            ),
            direction=payload.location.direction,
        ),
        type=payload.item,
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


class BuildPathPayload(pydantic.BaseModel):
    location: ports.EdgeCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


@router.post("/{game_id}/paths")
def build_path(
    game_id: uuid.UUID,
    nickname: Annotated[player.Nickname, fastapi.Depends(dependencies.get_player)],
    payload: BuildPathPayload,
    repository: Annotated[
        repository_module.InMemoryActiveGameRepository,
        fastapi.Depends(dependencies.get_repository),
    ],
    registry: Annotated[
        actions.ActionsRegistry, fastapi.Depends(dependencies.get_actions_registry)
    ],
    game_locks: Annotated[
        locks.GameLockManager, fastapi.Depends(dependencies.get_game_locks)
    ],
) -> ports.PlayedStonePath:
    try:
        services.apply_player_action(
            game_id,
            actions.BuildPathAction(
                by=nickname,
                coordinate=entities.Coordinate(
                    q=payload.location.hex_coord.q,
                    r=payload.location.hex_coord.r,
                    d=payload.location.direction,
                ),
            ),
            repository=repository,
            registry=registry,
            game_locks=game_locks,
        )
    except repository_module.ActiveGameDoesNotExistError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    except actions.InsufficientResourcesError as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except actions.InvalidPathLocation as e:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return ports.PlayedStonePath(
        owner=nickname,
        location=ports.EdgeCoordinate(
            hex_coord=ports.HexCoordinate(
                q=payload.location.hex_coord.q, r=payload.location.hex_coord.r
            ),
            direction=payload.location.direction,
        ),
    )
