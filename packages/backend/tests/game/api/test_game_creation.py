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


def test_create_includes_default_harbours(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    assert response.status_code == 201, response.text
    harbours = response.json()["harbours"]
    expected = [
        harbour.model_dump(mode="json") for harbour in teyuna_shared.grouped_harbours()
    ]
    assert harbours == expected


def test_create_with_custom_harbours(client: testclient.TestClient) -> None:
    custom_harbour = {
        "resource": "gold",
        "vertices": [
            {
                "hex_coord": {"q": 0, "r": 0},
                "direction": 0,
            },
            {
                "hex_coord": {"q": 0, "r": 0},
                "direction": 1,
            },
        ],
    }
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
            ],
            "conquistator_location": {"q": 0, "r": 0},
            "harbours": [custom_harbour],
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["conquistator_location"] == {"q": 0, "r": 0}
    assert len(payload["harbours"]) == 1
    assert payload["harbours"][0]["resource"] == "gold"
    expected = teyuna_shared.grouped_harbours(
        teyuna_shared.harbour_pairs_from_ports(
            (teyuna_shared.Harbour.model_validate(custom_harbour),)
        )
    )
    assert payload["harbours"] == [
        harbour.model_dump(mode="json") for harbour in expected
    ]
