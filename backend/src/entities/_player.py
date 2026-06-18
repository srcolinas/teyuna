import uuid
from typing import Annotated

import pydantic

from ._buildings import Settlement
from ._cards import WisdomCard


class Player(pydantic.BaseModel):
    id: uuid.UUID
    username: str
    played_wisdom_cards: list[WisdomCard]
    num_hidden_wisdom_cards: Annotated[int, pydantic.Field(ge=0, default=0)]
    num_resources: Annotated[int, pydantic.Field(ge=0)]
    available_settlements: list[Settlement]
    available_paths: Annotated[int, pydantic.Field(ge=0, le=15)]
