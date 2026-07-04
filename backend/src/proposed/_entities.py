import datetime
import uuid

import pydantic


class ProposedGame(pydantic.BaseModel):
    id: uuid.UUID
    max_players: int
    expires_at: datetime.datetime
    players: set[str]
