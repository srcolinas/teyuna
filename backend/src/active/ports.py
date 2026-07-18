import uuid
from typing import Annotated

import pydantic

from .. import player
from . import entities, actions


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
    owner: player.Nickname
    location: VertexCoordinate
    type: entities.SettlementType


class PlayedStonePath(pydantic.BaseModel):
    owner: player.Nickname
    location: EdgeCoordinate


class Player(pydantic.BaseModel):
    nickname: player.Nickname
    played_wisdom_cards: list[entities.WisdomCard] = []
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_terraces: Annotated[int, pydantic.Field(ge=0, le=5)] = 0
    available_great_terraces: Annotated[int, pydantic.Field(ge=0, le=4)] = 0
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)] = 0


class ActiveGame(pydantic.BaseModel):
    id: uuid.UUID
    map: tuple[Hex, ...]
    conquistator_location: HexCoordinate
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
    turn_order: tuple[player.Nickname, ...]
    phase: actions.GamePhaseName
