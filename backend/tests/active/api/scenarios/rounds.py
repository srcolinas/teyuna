import uuid

import fastapi.testclient as testclient

from src.active import entities

from .. import utils


type VertrexCoordinate = tuple[int, int, int]
type EdgeCoordinate = tuple[int, int, int]
type Token = str


def add_placement_round(
    client: testclient.TestClient,
    game_id: uuid.UUID,
    placements: list[tuple[Token, VertrexCoordinate, EdgeCoordinate]],
) -> None:
    for token, terrace, edge in placements:
        terrace = entities.canonical_vertex(*terrace)
        edge = entities.canonical_edge(*edge)
        utils.post_initial_placements(
            client,
            game_id,
            token,
            utils.build_initial_placement_payload(terrace, edge),
        )
