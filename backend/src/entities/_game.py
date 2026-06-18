import uuid

import pydantic

from ._board import EdgeCoordinate, Hex
from ._buildings import Settlement
from ._player import Player


class PlayedSettlement(Settlement):
    owner: uuid.UUID


class PlayedStonePath:
    owner: uuid.UUID
    location: EdgeCoordinate


class Game(pydantic.BaseModel):
    id: uuid.UUID
    map: list[Hex]
    conquistator_location: Hex
    players: list[Player]
    settlements: list[PlayedSettlement]
    paths: list[PlayedStonePath]
