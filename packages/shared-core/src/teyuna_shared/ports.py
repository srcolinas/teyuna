import datetime
import uuid
from collections.abc import Iterable
from typing import Annotated

import pydantic

from . import board, constants, entities


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
    victory_points: int
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


class ActiveTradeProposal(pydantic.BaseModel):
    id: uuid.UUID
    by: str
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: list[str]

    model_config = pydantic.ConfigDict(frozen=True)


class Harbour(pydantic.BaseModel):
    """A trading harbour spanning two docking vertices."""

    resource: entities.ResourceCard | None = None
    vertices: tuple[VertexCoordinate, VertexCoordinate]

    model_config = pydantic.ConfigDict(frozen=True)


class Game(pydantic.BaseModel):
    id: uuid.UUID
    turns_played: Annotated[int, pydantic.Field(ge=0)] = 0
    map: tuple[Hex, ...]
    conquistator_location: HexCoordinate
    harbours: tuple[Harbour, ...]
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
    trade_proposals: list[ActiveTradeProposal] = []
    to_discard_resources: dict[str, int] = pydantic.Field(default_factory=dict)


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4, default=3)]
    map: tuple[Hex, ...] | None = None
    conquistator_location: HexCoordinate | None = None
    harbours: tuple[Harbour, ...] | None = None


def _vertex_from_coordinate(coord: board.Coordinate) -> VertexCoordinate:
    return VertexCoordinate(
        hex_coord=HexCoordinate(q=coord.q, r=coord.r),
        direction=coord.d,
    )


def _coordinate_from_vertex(vertex: VertexCoordinate) -> board.Coordinate:
    return board.canonical_vertex(
        vertex.hex_coord.q, vertex.hex_coord.r, vertex.direction
    )


def grouped_harbours(
    pairs: Iterable[board.HarbourPair] | None = None,
) -> tuple[Harbour, ...]:
    """Convert harbour pairs (defaults if omitted) into API ``Harbour`` DTOs."""
    if pairs is None:
        pairs = board.default_harbour_pairs()
    return tuple(
        Harbour(
            resource=pair.resource,
            vertices=(
                _vertex_from_coordinate(pair.vertices[0]),
                _vertex_from_coordinate(pair.vertices[1]),
            ),
        )
        for pair in pairs
    )


def harbour_pairs_from_ports(
    harbours: Iterable[Harbour],
) -> tuple[board.HarbourPair, ...]:
    """Convert API harbours into board ``HarbourPair``s with canonical vertices."""
    return tuple(
        board.HarbourPair(
            resource=harbour.resource,
            vertices=(
                _coordinate_from_vertex(harbour.vertices[0]),
                _coordinate_from_vertex(harbour.vertices[1]),
            ),
        )
        for harbour in harbours
    )


def flatten_harbours(
    harbours: Iterable[Harbour],
) -> dict[board.Coordinate, entities.ResourceCard | None]:
    """Flatten API harbours into a canonical vertex → resource lookup."""
    return board.harbour_locations_from_pairs(harbour_pairs_from_ports(harbours))


class JoinGameResponse(pydantic.BaseModel):
    game: Game
    token: str
