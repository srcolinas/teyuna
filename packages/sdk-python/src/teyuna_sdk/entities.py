import dataclasses
import uuid
from collections.abc import Coroutine
from typing import Any, Protocol

from . import sdk


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerContext:
    """Authenticated seat context passed to an agent."""

    nickname: str
    client: sdk.AuthenticatedPlayerClient
    game_id: uuid.UUID


class PlayerBuilder(Protocol):
    """Async agent entrypoint: ``async def build(*, context: PlayerContext)``."""

    def __call__(
        self,
        *,
        context: PlayerContext,
    ) -> Coroutine[Any, Any, None]: ...
