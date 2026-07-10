from __future__ import annotations

import fastapi
from fastapi import testclient

from src.active import dependencies

from . import utils


def test_player_can_add_settlement(
    client: testclient.TestClient, app: fastapi.FastAPI
) -> None:
    game_id = utils.create_active_game(
        client, nicknames=["srcolinas-1", "srcolinas-2", "srcolinas-3"]
    )
    game = client.get(f"/active-games/{game_id}").json()
    player_in_turn = game["turn_order"][0]
    app.dependency_overrides[dependencies.get_player] = lambda: player_in_turn
    response = client.post(f"/active-games/{game_id}/settlements/0/0/0")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "location": {"hex_coord": {"q": 0, "r": 0}, "direction": 0},
        "type": "terrace",
        "owner": player_in_turn,
    }
