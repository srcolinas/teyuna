import collections
import uuid

import fastapi
import fastapi.testclient as testclient

import teyuna_core

from src.game import (
    entities,
    dependencies,
    player,
    repository as repository_module,
    actions,
)
from . import utils
import datetime


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")

    response = utils.post_action(
        client,
        uuid.uuid4(),
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 404, response.text


def test_returns_401_when_authorization_missing(
    client: testclient.TestClient,
) -> None:
    response = client.post(f"/games/{uuid.uuid4()}/actions", json={"kind": "advance"})

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "invalid token"


def test_returns_401_when_session_token_unknown(
    client: testclient.TestClient,
) -> None:
    response = client.post(
        f"/games/{uuid.uuid4()}/actions",
        json={"kind": "advance"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "player not found"


def test_returns_turn_order(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    response = client.get(f"/games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == list(game.turn_order)


def test_returns_turn_order_clockwise_from_active_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    order = list(game.turn_order)
    game.player_idx = 1
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    response = client.get(f"/games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == order[1:] + order[:1]


def test_returns_turn_order_counter_clockwise_during_second_placement(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    order = list(game.turn_order)
    game.player_idx = 2
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.SECOND_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    response = client.get(f"/games/{game_id}/turn-order")

    assert response.status_code == 200, response.text
    assert response.json() == order[2::-1] + order[:2:-1]


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    app.dependency_overrides[dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    other = game.turn_order[1]
    token = player.service().add(other)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 400, response.text


def test_rolls_dice_and_advances_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    active_player = game.active_player
    token = player.service().add(active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"]["kind"] == "advance"
    assert body["kind"] == "dice_roll"
    phase = body["next_phase"]
    assert phase in {
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR.value,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD.value,
        teyuna_core.GamePhaseName.DISCARD_RESOURCES.value,
    }
    turn_order = client.get(f"/games/{game_id}/turn-order").json()
    assert turn_order[0] == active_player
    stored_phase = repository.retrieve(game_id).phase
    assert stored_phase.value == phase
    assert game.active_player == active_player


def test_ends_trade_and_build_and_advances_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    active_player = game.active_player
    next_player = game.turn_order[1]
    token = player.service().add(active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "advance"},
        token=token,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"]["kind"] == "advance"
    assert body["kind"] == "ended_trade_and_build"
    assert body["next_phase"] == teyuna_core.GamePhaseName.DICE_ROLL.value
    assert body["next_player"] == next_player
    stored_phase = repository.retrieve(game_id).phase
    assert stored_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert game.active_player == next_player


def _create_game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=2
    )
    nicknames = ("srcolinas-0", "srcolinas-1", "srcolinas-2")
    game = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=mountains.q, r=mountains.r),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    return game
