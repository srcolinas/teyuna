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


def test_send_message_appears_on_events(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    event_broker = broker.EventBroker()
    app.dependency_overrides[dependencies.get_event_broker] = lambda: event_broker

    game_id, tokens = utils.create_active_game_with_tokens(client)
    sender = client.get(f"/games/{game_id}").json()["turn_order"][0]
    token = tokens[sender]
    text = "hello from the terrace"

    with _Server(app, port=18767) as base_url:
        with httpx2.Client(
            base_url=base_url, timeout=5.0, headers={"Authorization": f"Bearer {token}"}
        ) as http:
            with http.stream("GET", f"/games/{game_id}/events") as stream:
                lines = stream.iter_lines()
                _wait_until_connected(lines)

                response = http.post(
                    f"/games/{game_id}/messages",
                    json={"text": text},
                )
                assert response.status_code == 200, response.text

                sse_event = _read_first_sse_event(lines)

    assert sse_event["event"] == "message"
    assert sse_event["id"] == "0"
    assert sse_event["data"] == {
        "type": "message",
        "by": sender,
        "text": text,
    }


def test_sent_message_action_is_rejected(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    sender = client.get(f"/games/{game_id}").json()["turn_order"][0]

    response = utils.post_action(
        client,
        game_id,
        {"kind": "sent_message", "text": "hello"},
        token=tokens[sender],
    )

    assert response.status_code == 422


def test_empty_message_is_rejected(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    sender = client.get(f"/games/{game_id}").json()["turn_order"][0]

    response = client.post(
        f"/games/{game_id}/messages",
        json={"text": "   "},
        headers=utils.auth_headers(tokens[sender]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "message text must not be empty"


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
