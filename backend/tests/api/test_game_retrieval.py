import uuid

import fastapi.testclient as testclient


def test_200_if_active_game_exists(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text


def test_get_game_map_status_code(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/map")
    assert response.status_code == 200, response.text


def test_200_when_listing_players(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/players")
    assert response.status_code == 200, response.text


def test_get_player_200_for_existing_player(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/players/srcolinas-0")
    assert response.status_code == 200, response.text


def test_list_settlements_status_code(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/settlements")
    assert response.status_code == 200, response.text


def test_get_settlement_status_code(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/settlements/0/0/0")
    assert response.status_code == 200, response.text


def test_list_paths_status_code(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/paths")
    assert response.status_code == 200, response.text


def test_get_path_status_code(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/paths/0/0/0")
    assert response.status_code == 200, response.text


def test_404_if_active_game_doesnot_exists(client: testclient.TestClient) -> None:
    game_id = uuid.uuid4()
    response = client.get(f"/games/{game_id}")
    assert response.status_code == 404, response.text


def test_nonexistent_game_returns_404(client: testclient.TestClient) -> None:
    game_id = uuid.uuid4()
    endpoints = [
        f"/games/{game_id}",
        f"/games/{game_id}/map",
        f"/games/{game_id}/players",
        f"/games/{game_id}/players/srcolinas",
        f"/games/{game_id}/settlements",
        f"/games/{game_id}/settlements/0/0/0",
        f"/games/{game_id}/paths",
        f"/games/{game_id}/paths/0/0/0",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404, response.text


def test_proposed_game_returns_404(client: testclient.TestClient) -> None:
    game_id = _create_proposed_game(client)
    endpoints = [
        f"/games/{game_id}",
        f"/games/{game_id}/map",
        f"/games/{game_id}/players",
        f"/games/{game_id}/players/srcolinas-0",
        f"/games/{game_id}/settlements",
        f"/games/{game_id}/settlements/0/0/0",
        f"/games/{game_id}/paths",
        f"/games/{game_id}/paths/0/0/0",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404, response.text


def test_unknown_player_returns_400(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}/players/{uuid.uuid4()}")
    assert response.status_code == 404, response.text


def _create_active_game(
    client: testclient.TestClient,
    num_players: int = 3,
    usernames: list[str] | None = None,
) -> uuid.UUID:
    if usernames is None:
        usernames = [f"srcolinas-{i}" for i in range(num_players)]
    num_players = len(usernames)
    game_id = _create_proposed_game(client, num_players)
    for i in range(num_players):
        client.put(f"/games/{game_id}/players", json={"username": usernames[i]})
    return game_id


def _create_proposed_game(
    client: testclient.TestClient, num_players: int = 3
) -> uuid.UUID:
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    return uuid.UUID(game_id)
