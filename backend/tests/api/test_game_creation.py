import collections
import contextlib
import uuid

import fastapi.testclient as testclient
import pytest


@pytest.mark.parametrize("num_players,status", [(3, 201), (4, 201), (2, 422), (5, 422)])
def test_status_code(
    num_players: int, status: int, client: testclient.TestClient
) -> None:
    response = client.post("/games", json={"num_players": num_players})
    assert response.status_code == status, response.json()


@pytest.mark.parametrize("num_players", [3, 4])
def test_num_players(num_players: int, client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": num_players})
    payload = response.json()
    assert payload["num_players"] == num_players


def test_game_id_is_included(client: testclient.TestClient) -> None:
    response = client.post("/games", json={})
    print(response.text)
    payload = response.json()
    with not_raises(ValueError):
        uuid.UUID(payload["id"])


def test_quantities_of_resources(client: testclient.TestClient) -> None:
    response = client.post("/games", json={})
    payload = response.json()
    counts = collections.Counter(hex["type"] for hex in payload["map"])
    assert counts == {
        "mountains": 3,
        "quarries": 3,
        "highlands": 4,
        "valleys": 4,
        "jungle": 4,
        "desert": 1,
    }


def test_distribution_of_numbers(client: testclient.TestClient) -> None:
    response = client.post("/games", json={})
    payload = response.json()
    counts = collections.Counter(hex["number"] for hex in payload["map"])
    assert counts == {
        2: 1,
        3: 2,
        4: 2,
        5: 2,
        6: 2,
        7: 1,
        8: 2,
        9: 2,
        10: 2,
        11: 2,
        12: 1,
    }


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
