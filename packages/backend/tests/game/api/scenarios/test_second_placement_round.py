import fastapi.testclient as testclient


from .. import utils
from . import rounds, asserts
import teyuna_shared


def test_three_players_complete_first_placements(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(
        client, nicknames=["player-0", "player-1", "player-2"]
    )
    first, second, third = client.get(f"/games/{game_id}").json()["turn_order"]

    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[first], (-2, 0, 0), (-2, -1, 1)),
            (tokens[second], (-2, 0, 2), (-2, 0, 1)),
            (tokens[third], (-2, 0, 4), (-2, 0, 4)),
        ],
    )
    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[third], (1, 0, 4), (1, 0, 4)),
            (tokens[second], (1, 0, 2), (1, 0, 1)),
            (tokens[first], (1, 0, 0), (1, -1, 1)),
        ],
    )

    game = client.get(f"/games/{game_id}").json()
    assert game["phase"] == "dice roll"
    assert game["turn_order"] == [first, second, third]
    asserts.assert_settlements(
        game["settlements"],
        [
            (
                first,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(-2, 0, 0),
            ),
            (
                first,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(1, 0, 0),
            ),
            (
                second,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(-2, 0, 2),
            ),
            (
                second,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(1, 0, 2),
            ),
            (
                third,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(-2, 0, 4),
            ),
            (
                third,
                teyuna_shared.SettlementType.TERRACE,
                teyuna_shared.canonical_vertex(1, 0, 4),
            ),
        ],
    )
    asserts.assert_paths(
        game["paths"],
        [
            (first, teyuna_shared.canonical_edge(-2, -1, 1)),
            (first, teyuna_shared.canonical_edge(1, -1, 1)),
            (second, teyuna_shared.canonical_edge(-2, 0, 1)),
            (second, teyuna_shared.canonical_edge(1, 0, 1)),
            (third, teyuna_shared.canonical_edge(-2, 0, 4)),
            (third, teyuna_shared.canonical_edge(1, 0, 4)),
        ],
    )
    asserts.assert_players_attributes_equal(
        game["players"],
        {
            "available_terraces": 3,
            "available_great_terraces": 4,
            "available_paths": 13,
        },
    )
    second_terraces = {
        first: teyuna_shared.canonical_vertex(1, 0, 0),
        second: teyuna_shared.canonical_vertex(1, 0, 2),
        third: teyuna_shared.canonical_vertex(1, 0, 4),
    }
    asserts.assert_num_resources(
        game["players"],
        [
            (nick, asserts.count_adjacent_producing_hexes(game["map"], terrace))
            for nick, terrace in second_terraces.items()
        ],
    )
