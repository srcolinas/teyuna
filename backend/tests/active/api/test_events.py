import json
import threading
import time
from collections.abc import Iterator

import fastapi
import fastapi.testclient as testclient
import httpx
import uvicorn

from src.active import actions, broker, dependencies

from . import utils

_VALID_TERRACE = (0, -1, 2)
_VALID_PATH = (0, -1, 2)


def test_single_client_receives_action_event(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/active-games/{game_id}").json()["turn_order"][0]
    token = tokens[active_player]
    payload = utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH)

    with _Server(app, port=18765) as base_url:
        with httpx.Client(
            base_url=base_url, timeout=5.0, cookies={"session-token": token}
        ) as http:
            with http.stream("GET", f"/active-games/{game_id}/events") as stream:
                lines = stream.iter_lines()
                _wait_until_connected(lines)

                response = http.post(
                    f"/active-games/{game_id}/initial-placements",
                    json=payload,
                )
                assert response.status_code == 200, response.text

                event = _read_first_data_event(lines)

    assert event["succeeded"] is True
    assert event["phase"] == actions.GamePhaseName.FIRST_PLACEMENT.value
    assert event["error"] is None
    assert event["by"] == active_player


def test_disconnect_does_not_break_remaining_clients(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/active-games/{game_id}").json()["turn_order"][0]
    token = tokens[active_player]
    payload = utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH)

    with _Server(app, port=18766) as base_url:
        with httpx.Client(
            base_url=base_url, timeout=5.0, cookies={"session-token": token}
        ) as http:
            with http.stream("GET", f"/active-games/{game_id}/events") as leaving:
                with http.stream("GET", f"/active-games/{game_id}/events") as remaining:
                    leaving_lines = leaving.iter_lines()
                    remaining_lines = remaining.iter_lines()
                    _wait_until_connected(leaving_lines)
                    _wait_until_connected(remaining_lines)

                    leaving.close()

                    response = http.post(
                        f"/active-games/{game_id}/initial-placements",
                        json=payload,
                    )
                    assert response.status_code == 200, response.text

                    event = _read_first_data_event(remaining_lines)

    assert event["succeeded"] is True
    assert event["phase"] == actions.GamePhaseName.FIRST_PLACEMENT.value
    assert event["by"] == active_player


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


def _read_first_data_event(lines: Iterator[str]) -> dict:
    for line in lines:
        if line.startswith("data:"):
            return json.loads(line.removeprefix("data:").strip())
    raise AssertionError("expected an SSE data event")
