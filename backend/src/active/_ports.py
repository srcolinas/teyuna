import uuid
from typing import Annotated

import pydantic

from . import _entities


class PlayedSettlement(_entities.Settlement):
    owner: str


class PlayedStonePath(pydantic.BaseModel):
    owner: str
    location: _entities.EdgeCoordinate


class Player(pydantic.BaseModel):
    username: str
    played_wisdom_cards: list[_entities.WisdomCard] = []
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_settlements: list[_entities.Settlement] = []
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)] = 0


class ActiveGame(pydantic.BaseModel):
    id: uuid.UUID
    map: _entities.Map
    conquistator_location: _entities.HexCoordinate
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
    turn_order: tuple[_entities.Username, ...]
