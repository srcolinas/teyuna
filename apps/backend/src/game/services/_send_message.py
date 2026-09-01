import uuid
from typing import Protocol

import teyuna_core

_MAX_MESSAGE_LENGTH = 500


class InvalidMessageError(Exception):
    pass


class Broker(Protocol):
    async def publish(
        self, game_id: uuid.UUID, data: teyuna_core.AnyGameEvent
    ) -> None: ...


async def send_message(
    game_id: uuid.UUID,
    by: str,
    text: str,
    *,
    broker: Broker,
) -> None:
    cleaned = text.strip()
    if not cleaned:
        raise InvalidMessageError("message text must not be empty")
    if len(cleaned) > _MAX_MESSAGE_LENGTH:
        raise InvalidMessageError(
            f"message text must be at most {_MAX_MESSAGE_LENGTH} characters"
        )
    await broker.publish(
        game_id,
        teyuna_core.MessageEvent(by=by, text=cleaned),
    )
