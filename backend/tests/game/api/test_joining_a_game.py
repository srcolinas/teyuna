import asyncio
import datetime
import random
import uuid

import fastapi.testclient as testclient
import pytest

from src.game import (
    actions,
    broker as broker_module,
    entities,
    locks,
    repository,
    services,
)


@pytest.mark.parametrize("num_players,status", [(3, 200), (4, 200)])
def test_status_code(
    num_players: int, status: int, client: testclient.TestClient
) -> None:
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for i in range(num_players):
        response = client.post(
            f"/games/{game_id}/players", json={"nickname": f"srcolinas-{i}"}
        )
        assert response.status_code == status, response.text
    response = client.post(f"/games/{game_id}/players", json={"nickname": "failure"})
    assert response.status_code == 400, response.text


def test_identifty_token_is_retrieved(client: testclient.TestClient) -> None:
    num_players = 3
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    secrets = set()
    for i in range(num_players):
        response = client.post(
            f"/games/{game_id}/players", json={"nickname": f"srcolinas-{i}"}
        )
        header = response.headers["Set-Cookie"]
        assert "HttpOnly" in header, header
        assert "session-token" in client.cookies, client.cookies
        secrets.add(client.cookies["session-token"])
    assert len(secrets) == num_players


def test_player_can_be_added_before_expiration(
    client: testclient.TestClient,
    game_repository: repository.InMemoryGameRepository,
) -> None:
    board = services.generate_map()
    desert = next(h for h in board if h.type is entities.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=3,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(seconds=1),
    )
    game_id = game_repository.add(game)
    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 200, response.text
    nicknames = {p["nickname"] for p in response.json()["players"]}
    assert "srcolinas" in nicknames
    assert response.json()["available_slots"] == 2
    assert response.json()["phase"] == entities.GamePhaseName.LOBBY


def test_player_cannot_be_added_after_lobby_timeout(
    client: testclient.TestClient,
    game_repository: repository.InMemoryGameRepository,
) -> None:
    board = services.generate_map()
    desert = next(h for h in board if h.type is entities.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=entities.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=3,
        phase=entities.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        - datetime.timedelta(milliseconds=100),
    )
    game_id = game_repository.add(game)
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    registry.set_timeout(
        entities.GamePhaseName.LOBBY,
        datetime.timedelta(seconds=0),
        actions.timeouts.timeout_lobby,
    )

    asyncio.run(
        services.apply_timeout_if_due(
            game_id,
            repository=game_repository,
            registry=registry,
            game_locks=locks.GameLockManager(),
            broker=broker_module.EventBroker(),
            rng=random.Random(0),
        )
    )
    assert game_repository.retrieve(game_id).phase is entities.GamePhaseName.END_GAME

    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 400, response.text


def test_full_game_starts(client: testclient.TestClient) -> None:
    num_players = 3
    players = [f"srcolinas-{i}" for i in range(num_players)]
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    assert response.json()["phase"] == entities.GamePhaseName.LOBBY
    assert response.json()["map"]

    for nickname in players[:-1]:
        response = client.post(f"/games/{game_id}/players", json={"nickname": nickname})
        assert response.status_code == 200, response.text
        assert response.json()["phase"] == entities.GamePhaseName.LOBBY

    response = client.post(f"/games/{game_id}/players", json={"nickname": players[-1]})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["id"] == game_id
    assert payload["phase"] == entities.GamePhaseName.FIRST_PLACEMENT

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text
    assert sorted(response.json()["turn_order"]) == sorted(players)


def test_early_joiner_can_retrieve_game_by_same_id(
    client: testclient.TestClient,
) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    client.post(f"/games/{game_id}/players", json={"nickname": "early"})
    client.post(f"/games/{game_id}/players", json={"nickname": "mid"})
    response = client.post(f"/games/{game_id}/players", json={"nickname": "last"})
    assert response.status_code == 200, response.text
    assert response.json()["phase"] == entities.GamePhaseName.FIRST_PLACEMENT

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text
    assert response.json()["id"] == game_id
    assert response.json()["phase"] == entities.GamePhaseName.FIRST_PLACEMENT


def test_map_available_while_in_lobby(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.get(f"/games/{game_id}/map")
    assert response.status_code == 200, response.text
    assert len(response.json()) > 0


def test_action_fails_while_in_lobby(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    client.post(f"/games/{game_id}/players", json={"nickname": "only"})

    response = client.post(f"/games/{game_id}/turn-order")
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "game is not active"


def test_cannot_join_after_game_started(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    for i in range(3):
        client.post(f"/games/{game_id}/players", json={"nickname": f"p{i}"})

    response = client.post(f"/games/{game_id}/players", json={"nickname": "late"})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] in {"game already full", "game already started"}


def test_not_full_game_stays_in_lobby(client: testclient.TestClient) -> None:
    num_players = 3
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    for i in range(num_players - 1):
        response = client.post(
            f"/games/{game_id}/players",
            json={"nickname": f"srcolinas-{i}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["phase"] == entities.GamePhaseName.LOBBY
        assert response.json()["turn_order"] == []


def test_cannot_join_nonexistent_game(client: testclient.TestClient) -> None:
    response = client.post(
        f"/games/{uuid.uuid4()}/players",
        json={"nickname": "srcolinas"},
    )
    assert response.status_code == 404, response.text


def test_existing_player_can_rejoin_and_receive_a_new_token(
    client: testclient.TestClient,
) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 200, response.text
    first_token = client.cookies["session-token"]

    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 200, response.text
    assert client.cookies["session-token"] != first_token
    assert [player["nickname"] for player in response.json()["players"]] == [
        "srcolinas"
    ]


def test_existing_player_can_rejoin_after_game_started(
    client: testclient.TestClient,
) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    for nickname in ("early", "mid", "last"):
        response = client.post(f"/games/{game_id}/players", json={"nickname": nickname})
    assert response.json()["phase"] == entities.GamePhaseName.FIRST_PLACEMENT

    response = client.post(f"/games/{game_id}/players", json={"nickname": "early"})

    assert response.status_code == 200, response.text
    assert response.json()["phase"] == entities.GamePhaseName.FIRST_PLACEMENT
    assert "session-token" in client.cookies
