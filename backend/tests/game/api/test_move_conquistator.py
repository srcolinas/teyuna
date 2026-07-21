import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module

from . import utils
import datetime


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{uuid.uuid4()}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 404, response.text


def test_returns_conquistator_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository

    response = client.get(f"/games/{game_id}/conquistator")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "q": game.conquistator_location.q,
        "r": game.conquistator_location.r,
    }


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase = entities.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1
    game.phase = entities.GamePhaseName.DICE_PLAY_WARRIOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    app.dependency_overrides[game_dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 501, response.text


def test_moves_conquistator_and_returns_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)
    game = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    game.phase = entities.GamePhaseName.DICE_PLAY_WARRIOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.DICE_ROLL
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def test_moves_without_taking_resources_when_take_from_omitted(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)
    game = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    game.phase = entities.GamePhaseName.DICE_PLAY_WARRIOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 0, "r": 1}},
    )

    assert response.status_code == 200, response.text
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.DICE_ROLL
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 2


def test_returns_400_when_location_is_unchanged(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_warrior_phase(app)
    game = repository.retrieve(game_id)
    location = game.conquistator_location

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": location.q, "r": location.r}},
    )

    assert response.status_code == 400, response.text


def test_moves_conquistator_during_move_conquistator_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_move_conquistator_phase(
        app
    )
    game = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    game.phase = entities.GamePhaseName.MOVE_CONQUISTATOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def test_moves_conquistator_during_trade_and_build_play_warrior(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_phase(
        app, entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
    )
    game = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def _setup_warrior_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(app, entities.GamePhaseName.DICE_PLAY_WARRIOR)


def _setup_move_conquistator_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(app, entities.GamePhaseName.MOVE_CONQUISTATOR)


def _setup_phase(
    app: fastapi.FastAPI,
    phase: entities.GamePhaseName,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    game.players[active_player].cards[entities.WisdomCard.WARRIOR] = 1
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
    return repository, game_id, tokens, active_player, other


def _create_game() -> entities.Game:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=2)
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
