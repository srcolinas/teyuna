import pytest
import fastapi.testclient as testclient


from .. import utils
from . import rounds


@pytest.mark.flaky(reruns=3)
def test_advances_next_phase_same_turn(
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
    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[third], (1, 0, 4), (1, 0, 4)),
            (tokens[second], (1, 0, 2), (1, 0, 1)),
            (tokens[first], (1, 0, 0), (1, -1, 1)),
        ],
    )
    rounds.advance_phase(client, game_id, tokens[first])

    game = client.get(f"/active-games/{game_id}").json()
    assert game["phase"] == "trade and build"
    assert game["turn_order"] == [first, second, third]


@pytest.mark.flaky(reruns=3)
def test_advances_next_phase_next_turn(
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
    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[third], (1, 0, 4), (1, 0, 4)),
            (tokens[second], (1, 0, 2), (1, 0, 1)),
            (tokens[first], (1, 0, 0), (1, -1, 1)),
        ],
    )
    rounds.advance_phase(client, game_id, tokens[first])
    rounds.advance_phase(client, game_id, tokens[first])

    game = client.get(f"/active-games/{game_id}").json()
    assert game["phase"] == "dice roll"
    assert game["turn_order"] == [second, third, first]
