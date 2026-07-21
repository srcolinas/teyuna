import asyncio
import uuid

import pytest

from src.active import actions, broker


def _result(
    *,
    succeeded: bool = True,
    phase: actions.GamePhaseName = actions.GamePhaseName.DICE_ROLL,
    error: Exception | None = None,
) -> actions.ActionExecutionResult:
    return actions.ActionExecutionResult(succeeded=succeeded, phase=phase, error=error)


@pytest.mark.asyncio
async def test_single_subscriber_receives_events_in_order() -> None:
    event_broker = broker.EventBroker()
    game_id = uuid.uuid4()
    first = _result(phase=actions.GamePhaseName.FIRST_PLACEMENT)
    second = _result(phase=actions.GamePhaseName.DICE_ROLL)

    async def collect() -> list[broker.Event]:
        events: list[broker.Event] = []
        async for event in event_broker.iterate(game_id):
            events.append(event)
            if len(events) == 2:
                break
        return events

    collector = asyncio.create_task(collect())
    await asyncio.sleep(0)
    await event_broker.publish(game_id, first)
    await event_broker.publish(game_id, second)
    events = await collector

    assert [event.id for event in events] == [0, 1]
    assert [event.data for event in events] == [first, second]


@pytest.mark.asyncio
async def test_fan_out_delivers_to_all_subscribers() -> None:
    event_broker = broker.EventBroker()
    game_id = uuid.uuid4()
    payload = _result()

    async def take_one() -> broker.Event:
        async for event in event_broker.iterate(game_id):
            return event
        raise AssertionError("expected an event")

    first = asyncio.create_task(take_one())
    second = asyncio.create_task(take_one())
    await asyncio.sleep(0)
    await event_broker.publish(game_id, payload)

    assert (await first).data is payload
    assert (await second).data is payload


@pytest.mark.asyncio
async def test_late_subscriber_does_not_see_prior_events() -> None:
    event_broker = broker.EventBroker()
    game_id = uuid.uuid4()
    prior = _result(phase=actions.GamePhaseName.FIRST_PLACEMENT)
    later = _result(phase=actions.GamePhaseName.SECOND_PLACEMENT)

    await event_broker.publish(game_id, prior)

    async def take_one() -> broker.Event:
        async for event in event_broker.iterate(game_id):
            return event
        raise AssertionError("expected an event")

    waiter = asyncio.create_task(take_one())
    await asyncio.sleep(0)
    await event_broker.publish(game_id, later)
    event = await waiter

    assert event.id == 1
    assert event.data is later


@pytest.mark.asyncio
async def test_disconnect_unregisters_subscriber() -> None:
    event_broker = broker.EventBroker()
    game_id = uuid.uuid4()
    payload = _result()

    async def take_one() -> broker.Event:
        agen = event_broker.iterate(game_id)
        try:
            return await agen.__anext__()
        finally:
            await agen.aclose()

    async def hang() -> None:
        async for _ in event_broker.iterate(game_id):
            pass

    leaving = asyncio.create_task(hang())
    remaining = asyncio.create_task(take_one())
    await asyncio.sleep(0)

    assert len(event_broker._subscribers[game_id]) == 2

    leaving.cancel()
    with pytest.raises(asyncio.CancelledError):
        await leaving

    assert len(event_broker._subscribers[game_id]) == 1

    await event_broker.publish(game_id, payload)
    assert (await remaining).data is payload
    assert len(event_broker._subscribers[game_id]) == 0
