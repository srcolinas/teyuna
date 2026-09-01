import uuid
from typing import Any

import httpx2
from fastapi import testclient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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

    assert response.json()["game"]["phase"] == "first placement"
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
        tokens[nickname] = response.json()["token"]

    assert response.json()["game"]["phase"] == "first placement"
    return game_id, tokens


def post_action(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    action: dict[str, Any],
    *,
    token: str | None = None,
) -> httpx2.Response:
    headers = auth_headers(token) if token is not None else None
    return client.post(f"/games/{game_id}/actions", json=action, headers=headers)


def build_free_placement_action(
    terrace: tuple[int, int, int] | None = None,
    path: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    action: dict[str, Any] = {"kind": "free_placement"}
    if terrace is not None:
        tq, tr, td = terrace
        action["terrace"] = {"q": tq, "r": tr, "d": td}
    if path is not None:
        pq, pr, pd = path
        action["path"] = {"q": pq, "r": pr, "d": pd}
    return action


def post_initial_placements(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    token: str,
    action: dict[str, Any] | None = None,
) -> httpx2.Response:
    return post_action(
        client,
        game_id,
        action if action is not None else {"kind": "free_placement"},
        token=token,
    )
