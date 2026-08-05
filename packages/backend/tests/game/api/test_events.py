import json
import threading
import time
from collections.abc import Iterator

import fastapi
import fastapi.testclient as testclient
import httpx2
import uvicorn

from src.game import broker, dependencies

from . import utils
import teyuna_core

_VALID_TERRACE = (0, -1, 2)
_VALID_PATH = (0, -1, 2)


def test_single_client_receives_action_event(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/games/{game_id}").json()["turn_order"][0]
    token = tokens[active_player]
    action = utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH)

    with _Server(app, port=18765) as base_url:
        with httpx2.Client(
            base_url=base_url, timeout=5.0, headers={"Authorization": f"Bearer {token}"}
        ) as http:
            with http.stream("GET", f"/games/{game_id}/events") as stream:
                lines = stream.iter_lines()
                _wait_until_connected(lines)

                response = http.post(
                    f"/games/{game_id}/actions",
                    json=action,
                )
                assert response.status_code == 200, response.text

                sse_event = _read_first_sse_event(lines)

    assert sse_event["event"] == "successful_action"
    assert sse_event["id"] == "0"
    event = sse_event["data"]
    assert event["type"] == "successful_action"
    assert event["by"] == active_player
    assert event["due_to_timeout"] is False
    event = event["result"]
    assert event["error"] is None
    assert event["previous_phase"] == teyuna_core.GamePhaseName.FIRST_PLACEMENT.value
    assert event["next_phase"] == teyuna_core.GamePhaseName.FIRST_PLACEMENT.value
    assert event["action"]["kind"] == "free_placement"
    assert "by" not in event["action"]
    assert event["action"]["terrace"] == [0, -1, 2]
    assert event["action"]["path"] == [0, -1, 2]
    game_after = client.get(f"/games/{game_id}").json()
    assert event["next_player"] == game_after["turn_order"][0]


def test_disconnect_does_not_break_remaining_clients(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/games/{game_id}").json()["turn_order"][0]
    token = tokens[active_player]
    action = utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH)

    with _Server(app, port=18766) as base_url:
        with httpx2.Client(
            base_url=base_url, timeout=5.0, headers={"Authorization": f"Bearer {token}"}
        ) as http:
            with http.stream("GET", f"/games/{game_id}/events") as leaving:
                with http.stream("GET", f"/games/{game_id}/events") as remaining:
                    leaving_lines = leaving.iter_lines()
                    remaining_lines = remaining.iter_lines()
                    _wait_until_connected(leaving_lines)
                    _wait_until_connected(remaining_lines)

                    leaving.close()

                    response = http.post(
                        f"/games/{game_id}/actions",
                        json=action,
                    )
                    assert response.status_code == 200, response.text

                    sse_event = _read_first_sse_event(remaining_lines)

    assert sse_event["event"] == "successful_action"
    assert sse_event["id"] == "0"
    event = sse_event["data"]
    assert event["type"] == "successful_action"
    event = event["result"]
    assert event["error"] is None
    assert event["previous_phase"] == teyuna_core.GamePhaseName.FIRST_PLACEMENT.value
    assert event["next_phase"] == teyuna_core.GamePhaseName.FIRST_PLACEMENT.value
    assert event["action"]["kind"] == "free_placement"
    assert "by" not in event["action"]


def test_invalid_action_publishes_failed_event_and_keeps_http_error(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/games/{game_id}").json()["turn_order"][0]
    token = tokens[active_player]

    with _Server(app, port=18768) as base_url:
        with httpx2.Client(
            base_url=base_url, timeout=5.0, headers={"Authorization": f"Bearer {token}"}
        ) as http:
            with http.stream("GET", f"/games/{game_id}/events") as stream:
                lines = stream.iter_lines()
                _wait_until_connected(lines)

                response = http.post(
                    f"/games/{game_id}/actions",
                    json={"kind": "buy_wisdom_card"},
                )
                assert response.status_code == 400

                sse_event = _read_first_sse_event(lines)

    assert sse_event["event"] == "failed_action"
    assert sse_event["id"] == "0"
    event = sse_event["data"]
    assert event["type"] == "failed_action"
    assert event["by"] == active_player
    assert event["due_to_timeout"] is False
    assert event["action"] == {"kind": "buy_wisdom_card"}
    assert event["error"] == response.json()["detail"]


class _Server:
    def __init__(self, app: fastapi.FastAPI, port: int) -> None:
        self._config = uvicorn.Config(
            app, host="127.0.0.1", port=port, log_level="error"
        )
        self._server = uvicorn.Server(self._config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def __enter__(self) -> str:
        self._thread.start()
        deadline = time.monotonic() + 5
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("uvicorn failed to start")
            time.sleep(0.01)
        return f"http://127.0.0.1:{self._config.port}"

    def __exit__(self, *args: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


def _wait_until_connected(lines: Iterator[str]) -> None:
    for line in lines:
        if line.startswith(":"):
            return
    raise AssertionError("expected an SSE connection comment")


def _read_first_sse_event(lines: Iterator[str]) -> dict:
    event: dict = {}
    for line in lines:
        if line.startswith("event:"):
            event["event"] = line.removeprefix("event:").strip()
        elif line.startswith("id:"):
            event["id"] = line.removeprefix("id:").strip()
        elif line.startswith("data:"):
            event["data"] = json.loads(line.removeprefix("data:").strip())
        elif not line and "data" in event:
            return event
    raise AssertionError("expected an SSE data event")
