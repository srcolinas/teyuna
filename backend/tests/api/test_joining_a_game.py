import fastapi.testclient as testclient
import pytest


@pytest.mark.parametrize("num_players,status", [(3, 200), (4, 200)])
def test_status_code(
    num_players: int, status: int, client: testclient.TestClient
) -> None:
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for _ in range(num_players):
        response = client.put(
            f"/games/{game_id}/players", json={"username": "srcolinas"}
        )
        assert response.status_code == status, response.text
    response = client.put(f"/games/{game_id}/players", json={"username": "failure"})
    assert response.status_code == 400, response.text
