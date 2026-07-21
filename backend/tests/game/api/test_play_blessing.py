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

    response = client.post(
        f"/games/{uuid.uuid4()}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)
    game = repository.retrieve(game_id)
    game.phase = entities.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_called_during_mamo_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)
    game = repository.retrieve(game_id)
    game.phase = entities.GamePhaseName.DICE_PLAY_MAMO
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other = _setup_blessed_phase(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)
    app.dependency_overrides[game_dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_supply_is_insufficient(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)
    game = repository.retrieve(game_id)
    game.resource_supply[entities.ResourceCard.WOOD] = 0
    game.phase = entities.GamePhaseName.DICE_PLAY_BLESSED
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.WOOD.value,
            ]
        },
    )

    assert response.status_code == 400, response.text


def test_takes_two_resources_from_supply(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body[entities.ResourceCard.WOOD.value] == 1
    assert body[entities.ResourceCard.STONE.value] == 1

    stored = repository.retrieve(game_id)
    assert stored.phase is entities.GamePhaseName.DICE_ROLL


def test_takes_two_resources_during_trade_and_build_play_blessed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(
        app, phase=entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/wisdom-cards/blessing",
        json={
            "resources": [
                entities.ResourceCard.WOOD.value,
                entities.ResourceCard.STONE.value,
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body[entities.ResourceCard.WOOD.value] == 1
    assert body[entities.ResourceCard.STONE.value] == 1

    stored = repository.retrieve(game_id)
    assert stored.phase is entities.GamePhaseName.TRADE_AND_BUILD


def _setup_blessed_phase(
    app: fastapi.FastAPI,
    phase: entities.GamePhaseName = entities.GamePhaseName.DICE_PLAY_BLESSED,
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
    game.players[active_player].cards[entities.WisdomCard.BLESSING_OF_ALUNA] = 1
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
