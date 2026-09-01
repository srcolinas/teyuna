import uuid

import pytest

import teyuna_core

from src.game import services


class RecordingBroker:
    def __init__(self) -> None:
        self.events: list[teyuna_core.AnyGameEvent] = []

    async def publish(self, game_id: uuid.UUID, data: teyuna_core.AnyGameEvent) -> None:
        self.events.append(data)


@pytest.mark.asyncio
async def test_sends_message() -> None:
    broker = RecordingBroker()
    game_id = uuid.uuid4()

    await services.send_message(game_id, "alice", "hello", broker=broker)

    assert broker.events == [
        teyuna_core.MessageEvent(by="alice", text="hello"),
    ]


@pytest.mark.asyncio
async def test_strips_whitespace() -> None:
    broker = RecordingBroker()
    game_id = uuid.uuid4()

    await services.send_message(game_id, "alice", "  hello  ", broker=broker)

    assert broker.events == [
        teyuna_core.MessageEvent(by="alice", text="hello"),
    ]


@pytest.mark.asyncio
async def test_rejects_empty_text() -> None:
    broker = RecordingBroker()
    game_id = uuid.uuid4()

    with pytest.raises(services.InvalidMessageError, match="must not be empty"):
        await services.send_message(game_id, "alice", "   ", broker=broker)

    assert broker.events == []


@pytest.mark.asyncio
async def test_rejects_too_long_text() -> None:
    broker = RecordingBroker()
    game_id = uuid.uuid4()

    with pytest.raises(
        services.InvalidMessageError, match="must be at most 500 characters"
    ):
        await services.send_message(game_id, "alice", "x" * 501, broker=broker)

    assert broker.events == []
