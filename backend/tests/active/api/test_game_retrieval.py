import uuid

import fastapi.testclient as testclient

from . import utils


def test_200_if_active_game_exists(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}")
    assert response.status_code == 200, response.text


def test_get_game_map_status_code(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/map")
    assert response.status_code == 200, response.text


def test_200_when_listing_players(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/players")
    assert response.status_code == 200, response.text


def test_get_player_200_for_existing_player(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/players/srcolinas-0")
    assert response.status_code == 200, response.text


def test_list_settlements_status_code(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/settlements")
    assert response.status_code == 200, response.text


def test_get_settlement_status_code(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/settlements/0/0/0")
    assert response.status_code == 200, response.text


def test_list_paths_status_code(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/paths")
    assert response.status_code == 200, response.text


def test_get_path_status_code(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/paths/0/0/0")
    assert response.status_code == 200, response.text


def test_404_if_active_game_doesnot_exists(client: testclient.TestClient) -> None:
    game_id = uuid.uuid4()
    response = client.get(f"/active-games/{game_id}")
    assert response.status_code == 404, response.text


def test_nonexistent_game_returns_404(client: testclient.TestClient) -> None:
    game_id = uuid.uuid4()
    endpoints = [
        f"/active-games/{game_id}",
        f"/active-games/{game_id}/map",
        f"/active-games/{game_id}/players",
        f"/active-games/{game_id}/players/srcolinas",
        f"/active-games/{game_id}/settlements",
        f"/active-games/{game_id}/settlements/0/0/0",
        f"/active-games/{game_id}/paths",
        f"/active-games/{game_id}/paths/0/0/0",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404, response.text


def test_unknown_player_returns_400(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}/players/{uuid.uuid4()}")
    assert response.status_code == 404, response.text


def test_map_retrieval_matches_game(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}")
    game = response.json()
    response = client.get(f"/active-games/{game_id}/map")
    map = response.json()
    assert game["map"] == map


def test_players_retrieval_matches_game(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}")
    game = response.json()
    response = client.get(f"/active-games/{game_id}/players")
    players = response.json()
    assert game["players"] == players


def test_paths_retrieval_matches_game(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    response = client.get(f"/active-games/{game_id}")
    game = response.json()
    response = client.get(f"/active-games/{game_id}/paths")
    paths = response.json()
    assert game["paths"] == paths
