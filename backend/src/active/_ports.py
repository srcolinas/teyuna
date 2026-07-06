import uuid
from typing import Annotated

import pydantic

from .. import player
from . import _entities


class PlayedSettlement(_entities.Settlement):
    owner: player.Nickname


class PlayedStonePath(pydantic.BaseModel):
    owner: player.Nickname
    location: _entities.EdgeCoordinate


class Player(pydantic.BaseModel):
    nickname: player.Nickname
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
    turn_order: tuple[player.Nickname, ...]
