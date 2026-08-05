import datetime
import uuid
from collections.abc import Iterable
from typing import Annotated

import pydantic

from . import board, constants, entities


class Hex(pydantic.BaseModel):
    """A hex tile on the game board."""

    coordinate: board.HexLocation
    type: entities.HexType
    number: Annotated[int, pydantic.Field(default=None, ge=2, le=12)]

    model_config = pydantic.ConfigDict(frozen=True)


class PlayedSettlement(pydantic.BaseModel):
    owner: str
    location: board.Coordinate
    type: entities.SettlementType


class PlayedStonePath(pydantic.BaseModel):
    owner: str
    location: board.Coordinate


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
    vertices: tuple[board.Coordinate, board.Coordinate]

    model_config = pydantic.ConfigDict(frozen=True)


class Game(pydantic.BaseModel):
    id: uuid.UUID
    turns_played: Annotated[int, pydantic.Field(ge=0)] = 0
    map: tuple[Hex, ...]
    conquistator_location: board.HexLocation
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
    phase: Annotated[
        entities.GamePhaseName,
        pydantic.Field(
            description=(
                "Current game phase. Which action kinds are legal depends on this value; "
                "see each action type description."
            ),
        ),
    ]
    phase_deadline: Annotated[
        datetime.datetime | None,
        pydantic.Field(
            description=(
                "UTC deadline for the current phase. When reached, the server applies "
                "a timeout action for the phase."
            ),
        ),
    ]
    available_slots: Annotated[int, pydantic.Field(ge=0, le=4)]
    trade_proposals: list[ActiveTradeProposal] = []
    to_discard_resources: dict[str, int] = pydantic.Field(
        default_factory=dict,
        description=(
            "Nickname → number of resource cards that player must discard. "
            "Only those players may submit discard_resources during "
            "'discard resources'; others wait."
        ),
    )


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4, default=3)]
    map: tuple[Hex, ...] | None = None
    conquistator_location: board.HexLocation | None = None
    harbours: tuple[Harbour, ...] | None = None


def grouped_harbours(
    pairs: Iterable[board.HarbourPair] | None = None,
) -> tuple[Harbour, ...]:
    """Convert harbour pairs (defaults if omitted) into API ``Harbour`` DTOs."""
    if pairs is None:
        pairs = board.default_harbour_pairs()
    return tuple(
        Harbour(resource=pair.resource, vertices=pair.vertices) for pair in pairs
    )


def harbour_pairs_from_ports(
    harbours: Iterable[Harbour],
) -> tuple[board.HarbourPair, ...]:
    """Convert API harbours into board ``HarbourPair``s with canonical vertices."""
    return tuple(
        board.HarbourPair(
            resource=harbour.resource,
            vertices=(
                board.canonical_vertex(
                    harbour.vertices[0].q,
                    harbour.vertices[0].r,
                    harbour.vertices[0].d,
                ),
                board.canonical_vertex(
                    harbour.vertices[1].q,
                    harbour.vertices[1].r,
                    harbour.vertices[1].d,
                ),
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
