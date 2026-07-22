import datetime
import uuid
from typing import Annotated

import pydantic

from . import constants, entities


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
    type: entities.HexType
    number: Annotated[int, pydantic.Field(default=None, ge=2, le=12)]

    model_config = pydantic.ConfigDict(frozen=True)


class PlayedSettlement(pydantic.BaseModel):
    owner: str
    location: VertexCoordinate
    type: entities.SettlementType


class PlayedStonePath(pydantic.BaseModel):
    owner: str
    location: EdgeCoordinate


class Player(pydantic.BaseModel):
    nickname: str
    played_wisdom_cards: list[entities.WisdomCard] = []
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_terraces: Annotated[
        int, pydantic.Field(ge=0, le=constants.MAX_TERRACES)
    ] = 0
    available_great_terraces: Annotated[
        int, pydantic.Field(ge=0, le=constants.MAX_GREAT_TERRACES)
    ] = 0
    available_paths: Annotated[int, pydantic.Field(ge=0, le=constants.MAX_PATHS)] = 0


class PlayerHand(pydantic.BaseModel):
    """Private hand visible only to the authenticated player."""

    resources: dict[entities.ResourceCard, int]
    wisdom_cards: list[entities.WisdomCard]


class Game(pydantic.BaseModel):
    id: uuid.UUID
    map: tuple[Hex, ...]
    conquistator_location: HexCoordinate
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
    turn_order: Annotated[
        tuple[str, ...],
        pydantic.Field(
            max_length=4,
            description="""The order in which players will take turns, starting
            form the current turn's player and then continuing with the
            rest of the players in the order they will play their turn.
            Empty while the game is still in the lobby.""",
        ),
    ]
    phase: entities.GamePhaseName
    phase_deadline: datetime.datetime | None
    available_slots: Annotated[int, pydantic.Field(ge=0, le=4)]


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4, default=3)]
    map: tuple[Hex, ...] | None = None
    conquistator_location: HexCoordinate | None = None
