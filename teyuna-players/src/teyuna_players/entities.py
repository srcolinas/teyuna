from __future__ import annotations

import dataclasses
import datetime
import enum
import uuid
from collections.abc import Coroutine
from typing import Annotated, Any, Protocol

import pydantic

from . import sdk


class HexType(str, enum.Enum):
    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class ResourceCard(str, enum.Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


class WisdomCard(str, enum.Enum):
    WARRIOR = "warrior"
    BLESSING_OF_ALUNA = "blessing of aluna"
    WINDOM_OF_MAMO = "wisdom of mamo"
    PATHFINDER = "pathfinder"
    LEGACY_OF_THE_ELDERS = "legacy of the elders"


class SettlementType(str, enum.Enum):
    TERRACE = "terrace"
    GREAT_TERRACE = "great terrace"


class GamePhaseName(str, enum.Enum):
    LOBBY = "lobby"
    FIRST_PLACEMENT = "first placement"
    SECOND_PLACEMENT = "second placement"
    DICE_ROLL = "dice roll"
    DISCARD_RESOURCES = "discard resources"
    DICE_PLAY_WARRIOR = "dice play warrior"
    DICE_PLAY_MAMO = "dice play mamo"
    DICE_PLAY_BLESSED = "dice play blessed"
    DICE_PLAY_PATHFINDER = "dice play pathfinder"
    MOVE_CONQUISTATOR = "move conquistator"
    TRADE_AND_BUILD = "trade and build"
    TRADE_AND_BUILD_PLAY_WARRIOR = "trade and build play warrior"
    TRADE_AND_BUILD_PLAY_MAMO = "trade and build play mamo"
    TRADE_AND_BUILD_PLAY_BLESSED = "trade and build play blessed"
    TRADE_AND_BUILD_PLAY_PATHFINDER = "trade and build play pathfinder"
    END_GAME = "end game"


class HexCoordinate(pydantic.BaseModel):
    q: Annotated[int, pydantic.Field(ge=-2, le=2)]
    r: Annotated[int, pydantic.Field(ge=-2, le=2)]

    model_config = pydantic.ConfigDict(frozen=True)


class VertexCoordinate(pydantic.BaseModel):
    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class EdgeCoordinate(pydantic.BaseModel):
    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class Hex(pydantic.BaseModel):
    coordinate: HexCoordinate
    type: HexType
    number: Annotated[int | None, pydantic.Field(default=None, ge=2, le=12)] = None

    model_config = pydantic.ConfigDict(frozen=True)


class PlayedSettlement(pydantic.BaseModel):
    owner: str
    location: VertexCoordinate
    type: SettlementType

    model_config = pydantic.ConfigDict(frozen=True)


class PlayedStonePath(pydantic.BaseModel):
    owner: str
    location: EdgeCoordinate

    model_config = pydantic.ConfigDict(frozen=True)


class Player(pydantic.BaseModel):
    nickname: str
    played_wisdom_cards: list[WisdomCard] = pydantic.Field(default_factory=list)
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_terraces: Annotated[int, pydantic.Field(ge=0, le=5)] = 0
    available_great_terraces: Annotated[int, pydantic.Field(ge=0, le=4)] = 0
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)] = 0

    model_config = pydantic.ConfigDict(frozen=True)


class TradeProposal(pydantic.BaseModel):
    id: uuid.UUID
    by: str
    offer: dict[ResourceCard, int]
    request: dict[ResourceCard, int]
    to: set[str]

    model_config = pydantic.ConfigDict(frozen=True)


class Game(pydantic.BaseModel):
    id: uuid.UUID
    map: tuple[Hex, ...]
    conquistator_location: HexCoordinate
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
    turn_order: tuple[str, ...]
    phase: GamePhaseName
    phase_deadline: datetime.datetime | None
    available_slots: Annotated[int, pydantic.Field(ge=0, le=4)]

    model_config = pydantic.ConfigDict(frozen=True)


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4)] = 3
    map: tuple[Hex, ...] | None = None
    conquistator_location: HexCoordinate | None = None

    model_config = pydantic.ConfigDict(frozen=True)


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerContext:
    nickname: str
    client: sdk.AuthenticatedPlayerClient
    game_id: uuid.UUID


class PlayerBuilder(Protocol):
    def __call__(
        self,
        *,
        context: PlayerContext,
    ) -> Coroutine[Any, Any, None]: ...
