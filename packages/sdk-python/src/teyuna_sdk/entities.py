import dataclasses
import uuid
from collections.abc import Coroutine
from typing import Any, Protocol

from . import sdk


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerContext:
    nickname: str
    client: sdk.AuthenticatedPlayerClient
    game_id: uuid.UUID


class PlayerBuilder(Protocol):
    def __call__(
        self,
        *,
        context: PlayerContext,
    ) -> Coroutine[Any, Any, None]: ...
