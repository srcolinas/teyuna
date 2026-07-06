import uuid

from fastapi import testclient


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
