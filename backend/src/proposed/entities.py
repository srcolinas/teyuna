import datetime
import uuid

import pydantic

from .. import player


class ProposedGame(pydantic.BaseModel):
    id: uuid.UUID
    max_players: int
    expires_at: datetime.datetime
    players: set[player.Nickname]
