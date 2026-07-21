import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module
import datetime


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)
    path = entities.canonical_edge(0, 0, 0)

    response = client.post(
        f"/games/{uuid.uuid4()}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": path.q, "r": path.r},
                    "direction": path.d,
                }
            ]
        },
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, first, _ = _setup_pathfinder_phase(
        app
    )
    game = repository.retrieve(game_id)
    game.phase = entities.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": first.q, "r": first.r},
                    "direction": first.d,
                }
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, first, _ = _setup_pathfinder_phase(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": first.q, "r": first.r},
                    "direction": first.d,
                }
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, first, _ = _setup_pathfinder_phase(
        app
    )
    app.dependency_overrides[game_dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": first.q, "r": first.r},
                    "direction": first.d,
                }
            ]
        },
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_invalid_path_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _, _ = _setup_pathfinder_phase(app)
    disconnected = entities.canonical_edge(1, 1, 1)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": disconnected.q, "r": disconnected.r},
                    "direction": disconnected.d,
                }
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_places_paths_and_returns_them(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, first, second = (
        _setup_pathfinder_phase(app)
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": first.q, "r": first.r},
                    "direction": first.d,
                },
                {
                    "hex_coord": {"q": second.q, "r": second.r},
                    "direction": second.d,
                },
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.DICE_ROLL
    assert first in game.players[active_player].paths
    assert second in game.players[active_player].paths


def test_places_paths_during_trade_and_build_play_pathfinder(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, first, second = (
        _setup_pathfinder_phase(
            app, phase=entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER
        )
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/pathfinder",
        json={
            "paths": [
                {
                    "hex_coord": {"q": first.q, "r": first.r},
                    "direction": first.d,
                },
                {
                    "hex_coord": {"q": second.q, "r": second.r},
                    "direction": second.d,
                },
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert first in game.players[active_player].paths
    assert second in game.players[active_player].paths


def _setup_pathfinder_phase(
    app: fastapi.FastAPI,
    phase: entities.GamePhaseName = entities.GamePhaseName.DICE_PLAY_PATHFINDER,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    entities.Coordinate,
    entities.Coordinate,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    game.players[active_player].cards[entities.WisdomCard.PATHFINDER] = 1

    terrace = entities.canonical_vertex(0, 0, 0)
    game.players[active_player].settlements[terrace] = entities.SettlementType.TERRACE
    first = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    v0, v1 = entities.vertices_of_edge(first)
    shared = v1 if v1 != terrace else v0
    second = next(
        e
        for e in entities.edges_adjacent_to_vertex(shared.q, shared.r, shared.d)
        if e != first
    )

    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = phase
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other, first, second


def _create_game() -> entities.Game:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    game = entities.Game(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=mountains.q, r=mountains.r),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in ("srcolinas-0", "srcolinas-1", "srcolinas-2")
        },
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    return game
