import contextlib
import uuid

import fastapi.testclient as testclient
import pytest


@pytest.mark.parametrize("num_players,status", [(3, 201), (4, 201), (2, 422), (5, 422)])
def test_status_code(
    num_players: int, status: int, client: testclient.TestClient
) -> None:
    response = client.post("/proposed-games", json={"num_players": num_players})
    assert response.status_code == status, response.json()


@pytest.mark.parametrize("num_players", [3, 4])
def test_num_players(num_players: int, client: testclient.TestClient) -> None:
    response = client.post("/proposed-games", json={"num_players": num_players})
    payload = response.json()
    assert payload["max_players"] == num_players


def test_game_id_is_included(client: testclient.TestClient) -> None:
    response = client.post("/proposed-games", json={})
    print(response.text)
    payload = response.json()
    with not_raises(ValueError):
        uuid.UUID(payload["id"])


@contextlib.contextmanager
def not_raises(ExpectedException):
    try:
        yield

    except ExpectedException:
        raise AssertionError(
            "Did raise exception {0} when it should not!".format(
                repr(ExpectedException)
            )
        )

    except Exception as e:
        raise AssertionError("An unexpected exception {0} raised.".format(repr(e)))
