import dataclasses
from typing import Annotated, Final, NamedTuple

import pydantic

import enum


class ResourceType(str, enum.Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


class BuildingType(str, enum.Enum):
    ROAD = "road"
    BOHIO = "bohio"
    TEMPLE = "temple"


class HexType(str, enum.Enum):
    SIERRA = "sierra"
    QUARRY = "quarry"
    HIGHLAND = "highland"
    VALLEY = "valley"
    JUNGLE = "jungle"


class DevelopmentCardType(str, enum.Enum):
    WARRIOR = "warrior"
    ABUNDANCE = "abundance"
    WISDOM = "wisdom"
    TRAIL = "trail"


class Location(NamedTuple):
    q: Annotated[int, pydantic.Field(ge=-2, le=2, strict=True)]
    r: Annotated[int, pydantic.Field(ge=-2, le=2, strict=True)]


DiceRollResult = Annotated[int, pydantic.Field(ge=2, le=12)]

class Hex(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    type: HexType
    number: DiceRollResult
    location: Location



class Hand(pydantic.BaseModel):
    resources: dict[ResourceType, int]
    developments: dict[DevelopmentCardType, int]


class Player(pydantic.BaseModel):
    username: str

    hand: Hand
    deployed_buildings: dict[Location, BuildingType]
    available_buildings: dict[BuildingType, int]


@dataclasses.dataclass
class GameState:
    hexes: list[Hex]
    players: list[Player]
    conquistator: Location
    dessert: Location

    active_player: Annotated[str, "The username of the active player"] = ""

