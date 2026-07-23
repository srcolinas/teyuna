import pprint
import uuid

import fastapi.testclient as testclient

from src.game import player

from .. import utils
import teyuna_shared


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
            utils.build_initial_placement_payload(terrace, edge),
        )
        assert response.status_code == 200, pprint.pformat(response.text)


def advance_phase(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    token: Token,
) -> tuple[teyuna_shared.GamePhaseName, player.Nickname]:
    response = client.post(
        f"/games/{game_id}/turn-order",
        headers=utils.auth_headers(token),
    )
    assert response.status_code == 200, pprint.pformat(response.text)
    state, active_player = response.json()
    return state, active_player
