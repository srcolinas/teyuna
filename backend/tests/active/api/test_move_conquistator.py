import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src import active, player
from src.active import actions, entities, repository as repository_module

from . import utils


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{uuid.uuid4()}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 404, response.text


def test_returns_conquistator_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository

    response = client.get(f"/active-games/{game_id}/conquistator")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "q": game.conquistator_location.q,
        "r": game.conquistator_location.r,
    }


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 403, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_PLAY_WARRIOR)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": 0}},
    )

    assert response.status_code == 501, response.text


def test_moves_conquistator_and_returns_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)
    game, _ = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    repository.update(game_id, game, actions.GamePhaseName.DICE_PLAY_WARRIOR)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def test_moves_without_taking_resources_when_take_from_omitted(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_warrior_phase(app)
    game, _ = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    repository.update(game_id, game, actions.GamePhaseName.DICE_PLAY_WARRIOR)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 0, "r": 1}},
    )

    assert response.status_code == 200, response.text
    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 2


def test_returns_400_when_location_is_unchanged(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_warrior_phase(app)
    game, _ = repository.retrieve(game_id)
    location = game.conquistator_location

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
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
    game, _ = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    repository.update(game_id, game, actions.GamePhaseName.MOVE_CONQUISTATOR)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def test_moves_conquistator_during_trade_and_build_play_warrior(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_phase(
        app, actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR
    )
    game, _ = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 2
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/conquistator",
        json={"location": {"q": 1, "r": -1}, "take_from": other},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"q": 1, "r": -1}

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[active_player].resources[entities.ResourceCard.WOOD] == 1


def _setup_warrior_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(app, actions.GamePhaseName.DICE_PLAY_WARRIOR)


def _setup_move_conquistator_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(app, actions.GamePhaseName.MOVE_CONQUISTATOR)


def _setup_phase(
    app: fastapi.FastAPI,
    phase: actions.GamePhaseName,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    game.players[active_player].cards[entities.WisdomCard.WARRIOR] = 1
    game_id = repository.add(game)
    repository.update(game_id, game, phase)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other


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
