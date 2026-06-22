import datetime
import uuid
from enum import Enum
from typing import Annotated, Self

import pydantic


class HexType(str, Enum):
    """Types of hex tiles on the board."""

    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class HexCoordinate(pydantic.BaseModel):
    """Axial coordinate for hex grid positioning.

    Uses the axial coordinate system (q, r) which is standard for hex grids.
    See: https://www.redblobgames.com/grids/hexagons/.
    """

    q: Annotated[
        int,
        pydantic.Field(
            ge=-2,
            le=2,
            description="0 along the top left to bottom right diagonal of the board, positives to the right",
        ),
    ]
    r: Annotated[
        int,
        pydantic.Field(
            ge=-2,
            le=2,
            description="0 along the horizontal axes of the board, positives to the bottom",
        ),
    ]

    model_config = pydantic.ConfigDict(frozen=True)

    @pydantic.model_validator(mode="after")
    def check_hex_is_valid(self) -> Self:
        if (self.q, self.r) in {(-2, -2), (-2, -1), (-1, -2), (1, 2), (2, 1), (2, 2)}:
            raise ValueError("Hex coordinate is invalid")
        return self


class VertexCoordinate(pydantic.BaseModel):
    """Coordinate for a vertex (corner) of a hex.

    A vertex is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top vertex, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class EdgeCoordinate(pydantic.BaseModel):
    """Coordinate for an edge (side) of a hex.

    An edge is identified by its adjacent hex and a direction (0-5).
    Direction 0 is the top-right edge, going clockwise.
    """

    hex_coord: HexCoordinate
    direction: Annotated[int, pydantic.Field(ge=0, le=5)]

    model_config = pydantic.ConfigDict(frozen=True)


class Hex(pydantic.BaseModel):
    """A hex tile on the game board."""

    coordinate: HexCoordinate
    type: HexType
    number: Annotated[int, pydantic.Field(default=None, ge=2, le=12)]

    model_config = pydantic.ConfigDict(frozen=True)


class ResourceCard(str, Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


class WisdomCard(str, Enum):
    WARRIOR = "warrior"
    BLESSING_OF_ALUNA = "blessing of aluna"
    WINDOM_OF_MAMO = "wisdom of mamo"
    PATHFINDER = "pathfinder"
    LEGACY_OF_THE_ELDERS = "legacy of the elders"


class SettlementType(str, Enum):
    TERRACE = "terrace"
    GREAT_TERRACE = "great terrace"


class Settlement(pydantic.BaseModel):
    location: VertexCoordinate
    type: SettlementType


class Player(pydantic.BaseModel):
    id: uuid.UUID
    username: str
    played_wisdom_cards: list[WisdomCard] = []
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_settlements: list[Settlement] = []
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)] = 0


class PlayedSettlement(Settlement):
    owner: uuid.UUID


class PlayedStonePath(pydantic.BaseModel):
    owner: uuid.UUID
    location: EdgeCoordinate


type Map = list[Hex]


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4, default=3)]


class GameCreated(pydantic.BaseModel):
    id: uuid.UUID
    map: Map
    num_players: Annotated[int, pydantic.Field(ge=3, le=4)]
    expiration: Annotated[
        datetime.datetime,
        pydantic.Field(
            description="participants should join before this or the game should be discarded"
        ),
    ]


class ActiveGame(pydantic.BaseModel):
    id: uuid.UUID
    map: Map
    conquistator_location: Hex
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
