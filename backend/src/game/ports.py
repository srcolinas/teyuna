import uuid
from typing import Annotated

import pydantic

from . import entities


class PlayedSettlement(entities.Settlement):
    owner: uuid.UUID


class PlayedStonePath(pydantic.BaseModel):
    owner: uuid.UUID
    location: entities.EdgeCoordinate


class CreateGameRequest(pydantic.BaseModel):
    num_players: Annotated[int, pydantic.Field(ge=3, le=4, default=3)]


class Player(pydantic.BaseModel):
    username: str
    played_wisdom_cards: list[entities.WisdomCard] = []
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0)] = 0
    num_resources: Annotated[int, pydantic.Field(ge=0)] = 0
    available_settlements: list[entities.Settlement] = []
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)] = 0


class ActiveGame(pydantic.BaseModel):
    id: uuid.UUID
    map: entities.Map
    conquistator_location: entities.Hex
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
