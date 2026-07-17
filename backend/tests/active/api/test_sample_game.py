import fastapi
import fastapi.testclient as testclient

from src import active
from src.active import actions, entities, repository as repository_module

from . import utils


def test_three_players_complete_initial_placements(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    game_id, tokens = utils.create_active_game_with_tokens(client)
    turn_order = client.get(f"/active-games/{game_id}").json()["turn_order"]
    player_0, player_1, player_2 = turn_order

    # First placement: clockwise through turn order.
    first_placements = {
        player_0: ((-2, 0, 0), (-2, -1, 1)),
        player_1: ((-2, 0, 2), (-2, 0, 1)),
        player_2: ((-2, 0, 4), (-2, 0, 4)),
    }
    for nickname in turn_order:
        terrace, path = first_placements[nickname]
        utils.post_initial_placements(
            client,
            game_id,
            tokens[nickname],
            utils.build_initial_placement_payload(terrace, path),
        )

    # Second placement: counter-clockwise through turn order.
    second_placements = {
        player_2: ((-2, 1, 2), (-2, 1, 1)),
        player_1: ((-2, 1, 4), (-2, 1, 4)),
        player_0: ((-2, 2, 2), (-2, 2, 1)),
    }
    for nickname in reversed(turn_order):
        terrace, path = second_placements[nickname]
        utils.post_initial_placements(
            client,
            game_id,
            tokens[nickname],
            utils.build_initial_placement_payload(terrace, path),
        )

    game, phase = repository.retrieve(game_id)

    assert phase is actions.GamePhaseName.END

    expected = {
        player_0: (
            first_placements[player_0],
            second_placements[player_0],
        ),
        player_1: (
            first_placements[player_1],
            second_placements[player_1],
        ),
        player_2: (
            first_placements[player_2],
            second_placements[player_2],
        ),
    }
    for nickname, placements in expected.items():
        settlements = game.players[nickname].settlements
        paths = game.players[nickname].paths
        for terrace, path in placements:
            terrace_coord = entities.canonical_vertex(*terrace)
            path_coord = entities.canonical_edge(*path)
            assert settlements[terrace_coord] is entities.SettlementType.TERRACE
            assert path_coord in paths
