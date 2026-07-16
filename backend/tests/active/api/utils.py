import uuid

import httpx
from fastapi import testclient


type InitialPlacementPayload = dict[str, dict[str, dict[str, int] | int]]


def create_active_game(
    client: testclient.TestClient,
    num_players: int = 3,
    nicknames: list[str] | None = None,
) -> uuid.UUID:
    if nicknames is None:
        nicknames = [f"srcolinas-{i}" for i in range(num_players)]

    proposed_game_id = create_proposed_game_and_add_players(client, nicknames[:-1])

    response = client.post(
        f"/proposed-games/{proposed_game_id}/players",
        json={"nickname": nicknames[num_players - 1]},
    )
    payload = response.json()
    game_id = uuid.UUID(payload["game"])
    return game_id


def create_active_game_with_tokens(
    client: testclient.TestClient,
    nicknames: list[str] | None = None,
) -> tuple[uuid.UUID, dict[str, str]]:
    if nicknames is None:
        nicknames = ["srcolinas-0", "srcolinas-1", "srcolinas-2"]

    proposed_game_id = create_proposed_game(client, len(nicknames))
    tokens: dict[str, str] = {}
    game_id: uuid.UUID | None = None
    for nickname in nicknames:
        response = client.post(
            f"/proposed-games/{proposed_game_id}/players",
            json={"nickname": nickname},
        )
        tokens[nickname] = client.cookies["session-token"]
        payload = response.json()
        if payload["game"] is not None:
            game_id = uuid.UUID(payload["game"])

    assert game_id is not None
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
) -> httpx.Response:
    client.cookies.set("session-token", token)
    return client.post(
        f"/active-games/{game_id}/initial-placements",
        json=payload,
    )


def create_proposed_game_and_add_players(
    client: testclient.TestClient,
    nicknames: list[str],
) -> uuid.UUID:
    game_id = create_proposed_game(client, len(nicknames) + 1)
    for name in nicknames:
        client.post(
            f"/proposed-games/{game_id}/players",
            json={"nickname": name},
        )
    return game_id


def create_proposed_game(
    client: testclient.TestClient, num_players: int = 3
) -> uuid.UUID:
    response = client.post("/proposed-games", json={"num_players": num_players})
    game_id = response.json()["id"]
    return uuid.UUID(game_id)
