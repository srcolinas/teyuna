from collections.abc import Mapping
from enum import Enum
from typing import Final, NamedTuple


class HexType(str, Enum):
    """Types of hex tiles on the board."""

    MOUNTAINS = "mountains"
    QUARRIES = "quarries"
    HIGHLANDS = "highlands"
    VALLEYS = "valleys"
    JUNGLE = "jungle"
    DESERT = "desert"


class ResourceCard(str, Enum):
    GOLD = "gold"
    STONE = "stone"
    COTTON = "cotton"
    MAIZE = "maize"
    WOOD = "wood"


HEX_TYPE_TO_RESOURCE: Final[dict[HexType, ResourceCard]] = {
    HexType.MOUNTAINS: ResourceCard.GOLD,
    HexType.QUARRIES: ResourceCard.STONE,
    HexType.HIGHLANDS: ResourceCard.COTTON,
    HexType.VALLEYS: ResourceCard.MAIZE,
    HexType.JUNGLE: ResourceCard.WOOD,
}

type ResourceCount = Mapping[ResourceCard, int]


class TradeProposal(NamedTuple):
    by: str
    offer: ResourceCount
    request: ResourceCount
    to: set[str]


class WisdomCard(str, Enum):
    WARRIOR = "warrior"
    BLESSING_OF_ALUNA = "blessing of aluna"
    WINDOM_OF_MAMO = "wisdom of mamo"
    PATHFINDER = "pathfinder"
    LEGACY_OF_THE_ELDERS = "legacy of the elders"


class SettlementType(str, Enum):
    TERRACE = "terrace"
    GREAT_TERRACE = "great terrace"


class MapHex(NamedTuple):
    """Internal hex tile on the game board (axial q/r)."""

    q: int
    r: int
    type: HexType
    number: int


class GamePhaseName(str, Enum):
    LOBBY = "lobby"
    FIRST_PLACEMENT = "first placement"
    SECOND_PLACEMENT = "second placement"
    DICE_ROLL = "dice roll"
    DISCARD_RESOURCES = "discard resources"
    DICE_PLAY_WARRIOR = "dice play warrior"
    DICE_PLAY_MAMO = "dice play mamo"
    DICE_PLAY_BLESSED = "dice play blessed"
    DICE_PLAY_PATHFINDER = "dice play pathfinder"
    MOVE_CONQUISTATOR = "move conquistator"
    TRADE_AND_BUILD = "trade and build"
    TRADE_AND_BUILD_PLAY_WARRIOR = "trade and build play warrior"
    TRADE_AND_BUILD_PLAY_MAMO = "trade and build play mamo"
    TRADE_AND_BUILD_PLAY_BLESSED = "trade and build play blessed"
    TRADE_AND_BUILD_PLAY_PATHFINDER = "trade and build play pathfinder"
    END_GAME = "end game"
