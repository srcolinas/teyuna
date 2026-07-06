from __future__ import annotations

import uuid

import fastapi
from fastapi import testclient

from src import active, player
from src.active import ports, entities

from . import utils


def test_player_can_add_settlement(
    client: testclient.TestClient, app: fastapi.FastAPI
) -> None:
    manager = FakeGameManager()
    app.dependency_overrides[active.get_game_manager] = lambda: manager
    proposed_game_id = utils.create_proposed_game_and_add_players(
        client, nicknames=["srcolinas-1", "srcolinas-2"]
    )
    response = client.post(
        f"/proposed-games/{proposed_game_id}/players",
        json={"nickname": "srcolinas-3"},
    )
    game_id = response.json()["game"]
    client.cookies.set("session-token", client.cookies["session-token"])
    response = client.post(f"/active-games/{game_id}/settlements/0/0/0")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "location": {"hex_coord": {"q": 0, "r": 0}, "direction": 0},
        "type": "terrace",
        "owner": "srcolinas-3",
    }
    assert manager.added["srcolinas-3"] == ports.PlayedSettlement(
        owner="srcolinas-3",
        location=ports.VertexCoordinate(
            hex_coord=ports.HexCoordinate(q=0, r=0), direction=0
        ),
        type=entities.SettlementType.TERRACE,
    )


class FakeGameManager(active.GameManager):
    def __init__(
        self,
        invalid_for: set[player.Nickname] | None = None,
    ) -> None:
        self.added: dict[player.Nickname, ports.PlayedSettlement] = {}
        self._invalid_for = invalid_for or set()
        super().__init__(active.InMemoryActiveGameRepository())

    def add_terrace(
        self,
        id: uuid.UUID,
        nickname: player.Nickname,
        *,
        q: int,
        r: int,
        direction: int,
    ) -> ports.PlayedSettlement:
        if nickname in self._invalid_for:
            raise ValueError
        self.added[nickname] = ports.PlayedSettlement(
            owner=nickname,
            location=ports.VertexCoordinate(
                hex_coord=ports.HexCoordinate(q=q, r=r), direction=direction
            ),
            type=entities.SettlementType.TERRACE,
        )
        return self.added[nickname]
