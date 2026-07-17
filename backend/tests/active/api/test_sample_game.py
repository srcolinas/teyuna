import fastapi
import fastapi.testclient as testclient

from src import active
from src.active import actions, entities, validations, repository as repository_module

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

    assert phase is actions.GamePhaseName.DICE_ROLL

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

    # First player plays warrior and moves the conquistator.
    game.players[player_0].cards[entities.WisdomCard.WARRIOR] = 1
    repository.update(game_id, game, phase)

    client.cookies.set("session-token", tokens[player_0])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )
    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.DICE_PLAY_WARRIOR.value

    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": 0}

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.conquistator_location == entities.HexLocation(q=1, r=0)
    assert game.players[player_0].cards[entities.WisdomCard.WARRIOR] == 0
    assert game.players[player_0].played_cards[entities.WisdomCard.WARRIOR] == 1
    assert game.active_player == player_0

    # Mamo: monopolize wood from another player.
    game.players[player_1].resources[entities.ResourceCard.WOOD] = 2
    game.players[player_0].cards[entities.WisdomCard.WINDOM_OF_MAMO] = 1
    repository.update(game_id, game, phase)

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WINDOM_OF_MAMO.value},
    )
    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.DICE_PLAY_MAMO.value

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )
    assert response.status_code == 200, response.text
    assert response.json()[entities.ResourceCard.WOOD.value] == 2

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[player_1].resources[entities.ResourceCard.WOOD] == 0
    assert game.players[player_0].played_cards[entities.WisdomCard.WINDOM_OF_MAMO] == 1

    # Blessed: take two resources from supply.
    game.players[player_0].cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
    repository.update(game_id, game, phase)

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.BLESSING_OF_ALUNA.value},
    )
    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.DICE_PLAY_BLESSED.value

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.STONE.value,
                entities.ResourceCard.MAIZE.value,
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()[entities.ResourceCard.STONE.value] == 1
    assert response.json()[entities.ResourceCard.MAIZE.value] == 1

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert (
        game.players[player_0].played_cards[entities.WisdomCard.BLESSING_OF_ALUNA] == 1
    )

    # Pathfinder: build two free roads extending the player's network.
    path_a, path_b = _two_connected_free_paths(game, player_0)
    game.players[player_0].cards[entities.WisdomCard.PATHFINDER] = 1
    repository.update(game_id, game, phase)

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.PATHFINDER.value},
    )
    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.DICE_PLAY_PATHFINDER.value

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": path_a.q, "r": path_a.r},
                    "direction": path_a.d,
                },
                {
                    "hex_coord": {"q": path_b.q, "r": path_b.r},
                    "direction": path_b.d,
                },
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert path_a in game.players[player_0].paths
    assert path_b in game.players[player_0].paths
    assert game.players[player_0].played_cards[entities.WisdomCard.PATHFINDER] == 1

    # Legacy: use card and remain in dice roll.
    game.players[player_0].cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    repository.update(game_id, game, phase)

    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.LEGACY_OF_THE_ELDERS.value},
    )
    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.DICE_ROLL.value

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[player_0].cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] == 0
    assert (
        game.players[player_0].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS]
        == 1
    )


def _two_connected_free_paths(
    game: entities.ActiveGame, nickname: str
) -> tuple[entities.Coordinate, entities.Coordinate]:
    player_state = game.players[nickname]
    first: entities.Coordinate | None = None
    for owned in player_state.paths:
        for vertex in entities.vertices_of_edge(owned):
            for edge in entities.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d):
                if validations.can_add_free_path_at(
                    target=edge,
                    free_edges=game.free_edges,
                    existing_settlements=player_state.settlements.locations(),
                    existing_paths=player_state.paths,
                    free_vertices=game.free_verticies,
                ):
                    first = edge
                    break
            if first is not None:
                break
        if first is not None:
            break
    assert first is not None

    provisional_paths = player_state.paths | {first}
    second: entities.Coordinate | None = None
    for vertex in entities.vertices_of_edge(first):
        for edge in entities.edges_adjacent_to_vertex(vertex.q, vertex.r, vertex.d):
            if edge == first:
                continue
            if validations.can_add_free_path_at(
                target=edge,
                free_edges=game.free_edges - {first},
                existing_settlements=player_state.settlements.locations(),
                existing_paths=provisional_paths,
                free_vertices=game.free_verticies,
            ):
                second = edge
                break
        if second is not None:
            break
    assert second is not None
    return first, second
