import uuid

import fastapi.testclient as testclient


def test_200_if_active_game_exists(client: testclient.TestClient) -> None:
    game_id = _create_active_game(client)
    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text


def test_404_if_active_game_doesnot_exists(client: testclient.TestClient) -> None:
    game_id = _create_proposed_game(client)
    response = client.get(f"/games/{game_id}")
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
