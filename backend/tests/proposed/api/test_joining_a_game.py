import fastapi.testclient as testclient
import pytest


@pytest.mark.parametrize("num_players,status", [(3, 200), (4, 200)])
def test_status_code(
    num_players: int, status: int, client: testclient.TestClient
) -> None:
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for i in range(num_players):
        response = client.post(
            f"/proposed-games/{game_id}/players", json={"nickname": f"srcolinas-{i}"}
        )
        assert response.status_code == status, response.text
    response = client.post(
        f"/proposed-games/{game_id}/players", json={"nickname": "failure"}
    )
    assert response.status_code == 400, response.text


def test_identifty_token_is_retrieved(client: testclient.TestClient) -> None:
    num_players = 3
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]
    secrets = set()
    for i in range(num_players):
        response = client.post(
            f"/proposed-games/{game_id}/players", json={"nickname": f"srcolinas-{i}"}
        )
        header = response.headers["Set-Cookie"]
        assert "HttpOnly" in header, header
        assert "session-token" in client.cookies, client.cookies
        secrets.add(client.cookies["session-token"])
    assert len(secrets) == num_players
