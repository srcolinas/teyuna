import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module
import datetime
import teyuna_shared


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    path = teyuna_shared.canonical_edge(0, 0, 0)

    response = client.post(
        f"/games/{uuid.uuid4()}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, path = _setup_trade_and_build(app)

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {tokens[other]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 400, response.text


def test_builds_path_and_returns_it(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner"] == active_player
    assert body["location"]["hex_coord"] == {"q": path.q, "r": path.r}
    assert body["location"]["direction"] == path.d

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert path in game.players[active_player].paths
    assert game.players[active_player].resources[teyuna_shared.ResourceCard.STONE] == 0
    assert game.players[active_player].resources[teyuna_shared.ResourceCard.WOOD] == 0


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].settlements[terrace] = (
        teyuna_shared.SettlementType.TERRACE
    )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_invalid_path_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    disconnected = teyuna_shared.canonical_edge(1, 1, 1)

    response = client.post(
        f"/games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": disconnected.q, "r": disconnected.r},
                "direction": disconnected.d,
            }
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_path_by_coordinate(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    path = teyuna_shared.canonical_edge(0, 0, 0)
    game.players[game.active_player].paths.add(path)
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository

    response = client.get(f"/games/{game_id}/paths/{path.q}/{path.r}/{path.d}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner"] == game.active_player
    assert body["location"]["hex_coord"] == {"q": path.q, "r": path.r}
    assert body["location"]["direction"] == path.d


def _setup_trade_and_build(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    teyuna_shared.Coordinate,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    terrace = teyuna_shared.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_shared.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[active_player].settlements[terrace] = (
        teyuna_shared.SettlementType.TERRACE
    )
    game.players[active_player].resources.update(
        {
            teyuna_shared.ResourceCard.STONE: 1,
            teyuna_shared.ResourceCard.WOOD: 1,
        }
    )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other, path


def _create_game() -> entities.Game:
    mountains = teyuna_shared.MapHex(
        q=0, r=0, type=teyuna_shared.HexType.MOUNTAINS, number=2
    )
    game = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_shared.HexLocation(q=mountains.q, r=mountains.r),
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
