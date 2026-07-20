import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src import active, player
from src.active import actions, entities, repository as repository_module
import datetime


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)
    path = entities.canonical_edge(0, 0, 0)

    response = client.post(
        f"/active-games/{uuid.uuid4()}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 404, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, path = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 403, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 400, response.text


def test_builds_path_and_returns_it(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner"] == active_player
    assert body["location"]["hex_coord"] == {"q": path.q, "r": path.r}
    assert body["location"]["direction"] == path.d

    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert path in game.players[active_player].paths
    assert game.players[active_player].resources[entities.ResourceCard.STONE] == 0
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 0


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].settlements[terrace] = (
        entities.SettlementType.TERRACE
    )
    game_id = repository.add(
        game, phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    )
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, path = _setup_trade_and_build(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": path.q, "r": path.r},
                "direction": path.d,
            }
        },
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_invalid_path_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    disconnected = entities.canonical_edge(1, 1, 1)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/paths",
        json={
            "location": {
                "hex_coord": {"q": disconnected.q, "r": disconnected.r},
                "direction": disconnected.d,
            }
        },
    )

    assert response.status_code == 400, response.text


def test_returns_path_by_coordinate(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    path = entities.canonical_edge(0, 0, 0)
    game.players[game.active_player].paths.add(path)
    game_id = repository.add(
        game, phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    )
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    response = client.get(f"/active-games/{game_id}/paths/{path.q}/{path.r}/{path.d}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner"] == game.active_player
    assert body["location"]["hex_coord"] == {"q": path.q, "r": path.r}
    assert body["location"]["direction"] == path.d


def _setup_trade_and_build(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    entities.Coordinate,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    terrace = entities.canonical_vertex(0, 0, 0)
    path = next(
        iter(entities.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[active_player].settlements[terrace] = entities.SettlementType.TERRACE
    game.players[active_player].resources.update(
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game_id = repository.add(
        game, phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    )
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other, path


def _create_game() -> entities.ActiveGame:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=2)
    return entities.ActiveGame(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=mountains.q, r=mountains.r),
        turn_order=("srcolinas-0", "srcolinas-1", "srcolinas-2"),
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
    )
