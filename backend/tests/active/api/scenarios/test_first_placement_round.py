import fastapi.testclient as testclient

from src.active import entities

from .. import utils
from . import rounds, asserts


def test_three_players_complete_first_placements(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(
        client, nicknames=["player-0", "player-1", "player-2"]
    )
    first, second, third = client.get(f"/active-games/{game_id}").json()["turn_order"]

    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[first], (-2, 0, 0), (-2, -1, 1)),
            (tokens[second], (-2, 0, 2), (-2, 0, 1)),
            (tokens[third], (-2, 0, 4), (-2, 0, 4)),
        ],
    )

    game = client.get(f"/active-games/{game_id}").json()
    assert game["phase"] == "second placement"
    assert game["turn_order"] == [third, second, first]
    asserts.assert_settlements(
        game["settlements"],
        [
            (
                first,
                entities.SettlementType.TERRACE,
                entities.canonical_vertex(-2, 0, 0),
            ),
            (
                second,
                entities.SettlementType.TERRACE,
                entities.canonical_vertex(-2, 0, 2),
            ),
            (
                third,
                entities.SettlementType.TERRACE,
                entities.canonical_vertex(-2, 0, 4),
            ),
        ],
    )
    asserts.assert_paths(
        game["paths"],
        [
            (first, entities.canonical_edge(-2, -1, 1)),
            (second, entities.canonical_edge(-2, 0, 1)),
            (third, entities.canonical_edge(-2, 0, 4)),
        ],
    )
    asserts.assert_players_attributes_equal(
        game["players"],
        {
            "available_terraces": 4,
            "available_great_terraces": 4,
            "available_paths": 14,
        },
    )
