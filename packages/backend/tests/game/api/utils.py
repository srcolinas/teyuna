import uuid

import httpx2
from fastapi import testclient


type InitialPlacementPayload = dict[str, dict[str, dict[str, int] | int]]


def create_active_game(
    client: testclient.TestClient,
    num_players: int = 3,
    nicknames: list[str] | None = None,
) -> uuid.UUID:
    if nicknames is None:
        nicknames = [f"srcolinas-{i}" for i in range(num_players)]

    response = client.post("/games", json={"num_players": num_players})
    game_id = uuid.UUID(response.json()["id"])
    for nickname in nicknames:
        response = client.post(
            f"/games/{game_id}/players",
            json={"nickname": nickname},
        )
        assert response.status_code == 200, response.text

    assert response.json()["phase"] == "first placement"
    return game_id


def create_active_game_with_tokens(
    client: testclient.TestClient,
    nicknames: list[str] | None = None,
) -> tuple[uuid.UUID, dict[str, str]]:
    if nicknames is None:
        nicknames = ["srcolinas-0", "srcolinas-1", "srcolinas-2"]

    response = client.post("/games", json={"num_players": len(nicknames)})
    game_id = uuid.UUID(response.json()["id"])
    tokens: dict[str, str] = {}
    for nickname in nicknames:
        response = client.post(
            f"/games/{game_id}/players",
            json={"nickname": nickname},
        )
        assert response.status_code == 200, response.text
        tokens[nickname] = client.cookies["session-token"]

    assert response.json()["phase"] == "first placement"
    return game_id, tokens


def build_initial_placement_payload(
    terrace: tuple[int, int, int],
    path: tuple[int, int, int],
) -> InitialPlacementPayload:
    tq, tr, td = terrace
    pq, pr, pd = path
    return {
        "terrace": {"hex_coord": {"q": tq, "r": tr}, "direction": td},
        "path": {"hex_coord": {"q": pq, "r": pr}, "direction": pd},
    }


def post_initial_placements(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    token: str,
    payload: InitialPlacementPayload,
) -> httpx2.Response:
    client.cookies.set("session-token", token)
    return client.post(
        f"/games/{game_id}/initial-placements",
        json=payload,
    )
