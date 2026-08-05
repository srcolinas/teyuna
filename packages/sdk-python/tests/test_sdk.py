import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest import mock

import httpx2
import teyuna_core

from teyuna_sdk import sdk


def test_stream_events_validates_any_game_event_json() -> None:
    game_id = uuid.uuid4()
    phase_event = teyuna_core.PhaseChangedEvent(
        previous_phase=teyuna_core.GamePhaseName.LOBBY,
        next_phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
    )
    success_event = teyuna_core.SuccessfulActionEvent(
        by="alice",
        due_to_timeout=False,
        action=teyuna_core.PlayerAction(),
        result=teyuna_core.ActionExecutionResult(
            previous_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            next_phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
            action=teyuna_core.PlayerAction(),
        ),
    )

    class _FakeSSEEvent:
        def __init__(self, data: str) -> None:
            self.data = data

    async def _aiter() -> AsyncIterator[Any]:
        yield _FakeSSEEvent("")
        yield _FakeSSEEvent(phase_event.model_dump_json())
        yield _FakeSSEEvent(success_event.model_dump_json())

    @asynccontextmanager
    async def fake_sse(*_args: Any, **_kwargs: Any) -> AsyncIterator[Any]:
        yield _aiter()

    client = sdk.GameClient("http://example.test", game_id)
    with mock.patch.object(sdk._http_client, "sse", fake_sse):

        async def collect() -> list[teyuna_core.AnyGameEvent]:
            return [event async for event in client.stream_events()]

        events = asyncio.run(collect())

    assert len(events) == 2
    assert isinstance(events[0], teyuna_core.PhaseChangedEvent)
    assert events[0] == phase_event
    assert isinstance(events[1], teyuna_core.SuccessfulActionEvent)
    assert events[1].by == "alice"
    assert isinstance(events[1].action, teyuna_core.PlayerAction)


def test_submit_action_posts_clean_action_json() -> None:
    game_id = uuid.uuid4()
    action = teyuna_core.MoveConquistatorAction(q=1, r=-1, from_player="bob")
    result = teyuna_core.MovedConquistatorResult(
        previous_phase=teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        next_phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        action=action,
        q=1,
        r=-1,
        from_player="bob",
    )
    posted: dict[str, Any] = {}

    async def fake_post(
        url: str, *, headers: dict[str, str], json: dict[str, Any]
    ) -> httpx2.Response:
        posted["url"] = url
        posted["headers"] = headers
        posted["json"] = json
        request = httpx2.Request("POST", url)
        return httpx2.Response(
            200, json=result.model_dump(mode="json"), request=request
        )

    client = sdk.GameClient("http://example.test", game_id)
    client._token = "test-token"
    with mock.patch.object(sdk._http_client, "post", fake_post):
        returned = asyncio.run(client.submit_action(action))

    assert posted["url"] == f"http://example.test/games/{game_id}/actions"
    assert posted["headers"] == {"Authorization": "Bearer test-token"}
    assert posted["json"] == action.model_dump(mode="json")
    assert "by" not in posted["json"]
    assert "due_to_timeout" not in posted["json"]
    assert isinstance(returned, teyuna_core.MovedConquistatorResult)
    assert returned.q == 1
