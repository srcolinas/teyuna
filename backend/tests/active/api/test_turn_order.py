import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src import active, player
from src.active import actions, entities, repository as repository_module


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)

    response = client.post(f"/active-games/{uuid.uuid4()}/turn-order")

    assert response.status_code == 404, response.text


def test_returns_401_when_session_cookie_missing(
    client: testclient.TestClient,
) -> None:
    response = client.post(f"/active-games/{uuid.uuid4()}/turn-order")

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "invalid token"


def test_returns_401_when_session_token_unknown(
    client: testclient.TestClient,
) -> None:
    client.cookies.set("session-token", "not-a-real-token")
    response = client.post(f"/active-games/{uuid.uuid4()}/turn-order")

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "player not found"


def test_returns_turn_order(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    response = client.get(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == list(game.turn_order)


def test_returns_turn_order_clockwise_from_active_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game.player_idx = 1
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    response = client.get(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == ["srcolinas-1", "srcolinas-2", "srcolinas-0"]


def test_returns_turn_order_counter_clockwise_during_second_placement(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game.player_idx = 2
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.SECOND_PLACEMENT)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    response = client.get(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == ["srcolinas-2", "srcolinas-1", "srcolinas-0"]


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_PLAY_WARRIOR)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 501, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    other = game.turn_order[1]
    token = player.service().add(other)

    client.cookies.set("session-token", token)
    response = client.post(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 403, response.text


def test_rolls_dice_and_advances_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    active_player = game.active_player
    token = player.service().add(active_player)

    client.cookies.set("session-token", token)
    response = client.post(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    phase, nickname = response.json()
    assert phase in {
        actions.GamePhaseName.MOVE_CONQUISTATOR,
        actions.GamePhaseName.TRADE_AND_BUILD,
    }
    assert nickname == active_player
    _, stored_phase = repository.retrieve(game_id)
    assert stored_phase == phase
    assert game.active_player == active_player


def test_ends_trade_and_build_and_advances_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    active_player = game.active_player
    next_player = game.turn_order[1]
    token = player.service().add(active_player)

    client.cookies.set("session-token", token)
    response = client.post(f"/active-games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    phase, nickname = response.json()
    assert phase == actions.GamePhaseName.DICE_ROLL
    assert nickname == next_player
    _, stored_phase = repository.retrieve(game_id)
    assert stored_phase is actions.GamePhaseName.DICE_ROLL
    assert game.active_player == next_player


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
