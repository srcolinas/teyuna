import uuid

import fastapi.testclient as testclient
import pytest

from ... import utils
import teyuna_shared


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
    assert payload["available_slots"] == num_players


def test_game_id_is_included(client: testclient.TestClient) -> None:
    response = client.post("/games", json={})
    payload = response.json()
    with utils.assert_not_raises(ValueError):
        uuid.UUID(payload["id"])


def test_create_with_custom_map_and_conquistator(
    client: testclient.TestClient,
) -> None:
    response = client.post(
        "/games",
        json={
            "num_players": 3,
            "map": [
                {
                    "coordinate": {"q": 0, "r": 0},
                    "type": teyuna_shared.HexType.DESERT.value,
                    "number": 7,
                },
                {
                    "coordinate": {"q": 1, "r": 0},
                    "type": teyuna_shared.HexType.MOUNTAINS.value,
                    "number": 6,
                },
            ],
            "conquistator_location": {"q": 0, "r": 0},
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["conquistator_location"] == {"q": 0, "r": 0}
    assert len(payload["map"]) == 2
    assert payload["map"][0]["type"] == teyuna_shared.HexType.DESERT.value
