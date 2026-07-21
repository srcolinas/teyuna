from starlette import testclient
import pytest

from . import utils


def test_rejects_connection_without_session_token(
    client: testclient.TestClient,
) -> None:
    game_id = utils.create_active_game(client)
    client.cookies.clear()

    with pytest.raises(testclient.WebSocketDenialResponse) as exc_info:
        with client.websocket_connect(f"/games/{game_id}/chat"):
            pass

    assert exc_info.value.status_code == 401


def test_rejects_connection_with_unknown_session_token(
    client: testclient.TestClient,
) -> None:
    game_id = utils.create_active_game(client)
    client.cookies.clear()

    with pytest.raises(testclient.WebSocketDenialResponse) as exc_info:
        with client.websocket_connect(
            f"/games/{game_id}/chat",
            headers=_session_cookie_header("not-a-real-token"),
        ):
            pass

    assert exc_info.value.status_code == 401


def test_broadcasts_message_to_all_clients(
    client: testclient.TestClient,
) -> None:
    nicknames = ["srcolinas-0", "srcolinas-1", "srcolinas-2"]
    game_id, tokens = utils.create_active_game_with_tokens(client, nicknames)
    url = f"/games/{game_id}/chat"
    expected = "srcolinas-0: hello everyone"

    with client.websocket_connect(
        url, headers=_session_cookie_header(tokens["srcolinas-0"])
    ) as ws_0:
        with client.websocket_connect(
            url, headers=_session_cookie_header(tokens["srcolinas-1"])
        ) as ws_1:
            with client.websocket_connect(
                url, headers=_session_cookie_header(tokens["srcolinas-2"])
            ) as ws_2:
                ws_0.send_text("hello everyone")
                assert ws_0.receive_text() == expected
                assert ws_1.receive_text() == expected
                assert ws_2.receive_text() == expected


def test_disconnect_does_not_break_remaining_clients(
    client: testclient.TestClient,
) -> None:
    nicknames = ["srcolinas-0", "srcolinas-1", "srcolinas-2"]
    game_id, tokens = utils.create_active_game_with_tokens(client, nicknames)
    url = f"/games/{game_id}/chat"

    with client.websocket_connect(
        url, headers=_session_cookie_header(tokens["srcolinas-0"])
    ) as ws_0:
        with client.websocket_connect(
            url, headers=_session_cookie_header(tokens["srcolinas-1"])
        ) as ws_1:
            ws_0.send_text("before leave")
            assert ws_0.receive_text() == "srcolinas-0: before leave"
            assert ws_1.receive_text() == "srcolinas-0: before leave"

        ws_0.send_text("still here")
        assert ws_0.receive_text() == "srcolinas-0: still here"


def test_messages_are_isolated_between_games(
    client: testclient.TestClient,
) -> None:
    game_a, tokens_a = utils.create_active_game_with_tokens(
        client, ["alice-0", "alice-1", "alice-2"]
    )
    game_b, tokens_b = utils.create_active_game_with_tokens(
        client, ["bob-0", "bob-1", "bob-2"]
    )
    url_a = f"/games/{game_a}/chat"
    url_b = f"/games/{game_b}/chat"

    with client.websocket_connect(
        url_a, headers=_session_cookie_header(tokens_a["alice-0"])
    ) as ws_a0:
        with client.websocket_connect(
            url_a, headers=_session_cookie_header(tokens_a["alice-1"])
        ) as ws_a1:
            with client.websocket_connect(
                url_b, headers=_session_cookie_header(tokens_b["bob-0"])
            ) as ws_b0:
                ws_a0.send_text("only in a")
                assert ws_a0.receive_text() == "alice-0: only in a"
                assert ws_a1.receive_text() == "alice-0: only in a"

                ws_b0.send_text("only in b")
                assert ws_b0.receive_text() == "bob-0: only in b"


def _session_cookie_header(token: str) -> dict[str, str]:
    return {"cookie": f"session-token={token}"}
