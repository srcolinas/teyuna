import pprint
import uuid

import fastapi.testclient as testclient

from src.game import player

from .. import utils
import teyuna_core


type VertrexCoordinate = tuple[int, int, int]
type EdgeCoordinate = tuple[int, int, int]
type Token = str


def add_placement_round(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    placements: list[tuple[Token, VertrexCoordinate, EdgeCoordinate]],
) -> None:
    for token, terrace, edge in placements:
        response = utils.post_initial_placements(
            client,
            game_id,
            token,
            utils.build_free_placement_action(terrace, edge),
        )
        assert response.status_code == 200, pprint.pformat(response.text)


def advance_phase(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    token: Token,
) -> tuple[teyuna_core.GamePhaseName, player.Nickname]:
    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )
    assert response.status_code == 200, pprint.pformat(response.text)
    body = response.json()
    active_player = body.get("next_player")
    if not active_player:
        game = client.get(f"/games/{game_id}").json()
        active_player = game["turn_order"][0] if game["turn_order"] else ""
    return teyuna_core.GamePhaseName(body["next_phase"]), active_player
