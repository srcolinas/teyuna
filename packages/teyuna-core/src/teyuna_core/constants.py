from collections.abc import Mapping
from typing import Final

from . import entities

MAX_TERRACES: Final[int] = 5
MAX_PATHS: Final[int] = 15
MAX_GREAT_TERRACES: Final[int] = 4

INVALID_HEX_COORDINATES: Final[set[tuple[int, int]]] = {
    (-2, -2),
    (-2, -1),
    (-1, -2),
    (1, 2),
    (2, 1),
    (2, 2),
}

RESOURCE_BANK_PER_TYPE: Final[int] = 19

WISDOM_DECK_COUNTS: Final[Mapping[entities.WisdomCard, int]] = {
    entities.WisdomCard.WARRIOR: 14,
    entities.WisdomCard.LEGACY_OF_THE_ELDERS: 5,
    entities.WisdomCard.PATHFINDER: 2,
    entities.WisdomCard.BLESSING_OF_ALUNA: 2,
    entities.WisdomCard.WINDOM_OF_MAMO: 2,
}

TERRACE_COST: Final[Mapping[entities.ResourceCard, int]] = {
    entities.ResourceCard.STONE: 1,
    entities.ResourceCard.WOOD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}

GREAT_TERRACE_COST: Final[Mapping[entities.ResourceCard, int]] = {
    entities.ResourceCard.GOLD: 3,
    entities.ResourceCard.MAIZE: 2,
}
PATH_COST: Final[Mapping[entities.ResourceCard, int]] = {
    entities.ResourceCard.STONE: 1,
    entities.ResourceCard.WOOD: 1,
}
WISDOM_CARD_COST: Final[Mapping[entities.ResourceCard, int]] = {
    entities.ResourceCard.GOLD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}

DEFAULT_TRADE_RATE: Final[int] = 4
GENERIC_HARBOUR_TRADE_RATE: Final[int] = 3
SPECIFIC_HARBOUR_TRADE_RATE: Final[int] = 2
