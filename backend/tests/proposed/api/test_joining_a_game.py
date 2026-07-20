import datetime
import uuid

import fastapi
import fastapi.testclient as testclient
import pytest

from src import active
from src.active import entities
from src.proposed import repository


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


def test_player_can_be_added_before_expiration(
    client: testclient.TestClient,
    proposed_repository: repository.InMemoryProposedGameRepository,
) -> None:
    game = proposed_repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    )
    response = client.post(
        f"/proposed-games/{game.id}/players", json={"nickname": "srcolinas"}
    )
    assert response.status_code == 200, response.text
    assert "srcolinas" in response.json()["proposed"]["players"]


def test_player_cannot_be_added_after_expiration(
    client: testclient.TestClient,
    proposed_repository: repository.InMemoryProposedGameRepository,
) -> None:
    game = proposed_repository.add(
        num_players=3,
        expires_at=datetime.datetime.now() - datetime.timedelta(milliseconds=100),
    )
    response = client.post(
        f"/proposed-games/{game.id}/players", json={"nickname": "srcolinas"}
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "game expired"


def test_full_game_starts(client: testclient.TestClient) -> None:
    num_players = 3
    players = [f"srcolinas-{i}" for i in range(num_players)]
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]

    for nickname in players[:-1]:
        response = client.post(
            f"/proposed-games/{game_id}/players", json={"nickname": nickname}
        )
        assert response.status_code == 200, response.text

    response = client.post(
        f"/proposed-games/{game_id}/players", json={"nickname": players[-1]}
    )
    assert response.status_code == 200, response.text
    active_game_id = response.json()["game"]
    assert active_game_id is not None

    response = client.get(f"/active-games/{active_game_id}")
    assert response.status_code == 200, response.text
    assert sorted(response.json()["turn_order"]) == sorted(players)


def test_not_full_game_is_not_started(client: testclient.TestClient) -> None:
    num_players = 3
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for i in range(num_players - 1):
        response = client.post(
            f"/proposed-games/{game_id}/players",
            json={"nickname": f"srcolinas-{i}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["game"] is None


def test_cannot_join_nonexistent_game(client: testclient.TestClient) -> None:
    response = client.post(
        f"/proposed-games/{uuid.uuid4()}/players",
        json={"nickname": "srcolinas"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "game doesn't exist"


def test_cannot_join_with_duplicate_nickname(client: testclient.TestClient) -> None:
    response = client.post("/proposed-games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.post(
        f"/proposed-games/{game_id}/players", json={"nickname": "srcolinas"}
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/proposed-games/{game_id}/players", json={"nickname": "srcolinas"}
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "nickname already exists"


class _ActiveRepositoryThatFailsAdd:
    def add(
        self, game: entities.ActiveGame, *, phase_deadline: datetime.datetime | None
    ) -> uuid.UUID:
        raise active.repository.ActiveGameDoesNotExistError


def test_returns_400_when_active_game_cannot_be_created(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    app.dependency_overrides[active.dependencies.get_repository] = (
        lambda: _ActiveRepositoryThatFailsAdd()
    )
    num_players = 3
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for i in range(num_players - 1):
        response = client.post(
            f"/proposed-games/{game_id}/players",
            json={"nickname": f"srcolinas-{i}"},
        )
        assert response.status_code == 200, response.text

    response = client.post(
        f"/proposed-games/{game_id}/players",
        json={"nickname": f"srcolinas-{num_players - 1}"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "game doesn't exist"
