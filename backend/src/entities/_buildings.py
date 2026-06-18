from enum import Enum

import pydantic

from ._board import EdgeCoordinate, VertexCoordinate


class SettlementType(str, Enum):
    TERRACE = "terrace"
    GREAT_TERRACE = "great terrace"


class Settlement(pydantic.BaseModel):
    location: VertexCoordinate
    type: SettlementType


type StonePath = EdgeCoordinate
