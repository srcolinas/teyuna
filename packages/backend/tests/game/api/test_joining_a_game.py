import asyncio
import datetime
import random
import uuid

import fastapi.testclient as testclient
import pytest

import teyuna_shared

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


def test_identity_token_is_retrieved(client: testclient.TestClient) -> None:
    num_players = 3
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    secrets = set()
    for i in range(num_players):
        response = client.post(
            f"/games/{game_id}/players", json={"nickname": f"srcolinas-{i}"}
        )
        body = response.json()
        assert "token" in body, body
        assert body["token"], body
        assert "Set-Cookie" not in response.headers
        secrets.add(body["token"])
    assert len(secrets) == num_players


def test_player_can_be_added_before_expiration(
    client: testclient.TestClient,
    game_repository: repository.InMemoryGameRepository,
) -> None:
    board = services.generate_map()
    desert = next(h for h in board if h.type is teyuna_shared.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=teyuna_shared.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=3,
        phase=teyuna_shared.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(seconds=1),
    )
    game_id = game_repository.add(game)
    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 200, response.text
    game = response.json()["game"]
    nicknames = {p["nickname"] for p in game["players"]}
    assert "srcolinas" in nicknames
    assert game["available_slots"] == 2
    assert game["phase"] == teyuna_shared.GamePhaseName.LOBBY


def test_player_cannot_be_added_after_lobby_timeout(
    client: testclient.TestClient,
    game_repository: repository.InMemoryGameRepository,
) -> None:
    board = services.generate_map()
    desert = next(h for h in board if h.type is teyuna_shared.HexType.DESERT)
    game = entities.Game(
        map=board,
        conquistator_location=teyuna_shared.HexLocation(q=desert.q, r=desert.r),
        players={},
        available_slots=3,
        phase=teyuna_shared.GamePhaseName.LOBBY,
        phase_deadline=datetime.datetime.now(datetime.UTC)
        - datetime.timedelta(milliseconds=100),
    )
    game_id = game_repository.add(game)
    registry = actions.ActionsRegistry()
    registry.register(teyuna_shared.GamePhaseName.LOBBY)(actions.handle_lobby_timeout)
    registry.set_timeout(
        teyuna_shared.GamePhaseName.LOBBY,
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
    assert (
        game_repository.retrieve(game_id).phase is teyuna_shared.GamePhaseName.END_GAME
    )

    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 400, response.text


def test_full_game_starts(client: testclient.TestClient) -> None:
    num_players = 3
    players = [f"srcolinas-{i}" for i in range(num_players)]
    response = client.post("/games", json={"num_players": num_players})
    game_id = response.json()["id"]
    assert response.json()["phase"] == teyuna_shared.GamePhaseName.LOBBY
    assert response.json()["map"]

    for nickname in players[:-1]:
        response = client.post(f"/games/{game_id}/players", json={"nickname": nickname})
        assert response.status_code == 200, response.text
        assert response.json()["game"]["phase"] == teyuna_shared.GamePhaseName.LOBBY

    response = client.post(f"/games/{game_id}/players", json={"nickname": players[-1]})
    assert response.status_code == 200, response.text
    payload = response.json()["game"]
    assert payload["id"] == game_id
    assert payload["phase"] == teyuna_shared.GamePhaseName.FIRST_PLACEMENT

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
    assert (
        response.json()["game"]["phase"] == teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    )

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text
    assert response.json()["id"] == game_id
    assert response.json()["phase"] == teyuna_shared.GamePhaseName.FIRST_PLACEMENT


def test_map_available_while_in_lobby(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.get(f"/games/{game_id}/map")
    assert response.status_code == 200, response.text
    assert len(response.json()) > 0


def test_action_fails_while_in_lobby(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.post(f"/games/{game_id}/players", json={"nickname": "only"})
    token = response.json()["token"]

    response = client.post(
        f"/games/{game_id}/actions",
        json={"kind": "advance"},
        headers={"Authorization": f"Bearer {token}"},
    )
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
        assert response.json()["game"]["phase"] == teyuna_shared.GamePhaseName.LOBBY
        assert response.json()["game"]["turn_order"] == []


def test_cannot_join_nonexistent_game(client: testclient.TestClient) -> None:
    response = client.post(
        f"/games/{uuid.uuid4()}/players",
        json={"nickname": "srcolinas"},
    )
    assert response.status_code == 404, response.text


def test_cannot_join_with_duplicate_nickname(client: testclient.TestClient) -> None:
    response = client.post("/games", json={"num_players": 3})
    game_id = response.json()["id"]
    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 200, response.text

    response = client.post(f"/games/{game_id}/players", json={"nickname": "srcolinas"})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "nickname already exists"
