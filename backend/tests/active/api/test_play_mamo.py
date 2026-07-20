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

    response = client.post(
        f"/active-games/{uuid.uuid4()}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_mamo_phase(app)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_ROLL,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_called_during_blessed_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_mamo_phase(app)
    repository.update(
        game_id,
        repository.retrieve(game_id).game,
        actions.GamePhaseName.DICE_PLAY_BLESSED,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 400, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other = _setup_mamo_phase(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 403, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_mamo_phase(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 501, response.text


def test_takes_all_of_resource_from_other_players(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_mamo_phase(app)
    game = repository.retrieve(game_id).game
    game.players[other].resources[entities.ResourceCard.WOOD] = 3
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.DICE_PLAY_MAMO,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 200, response.text
    assert response.json()[entities.ResourceCard.WOOD.value] == 3

    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 0


def test_takes_all_of_resource_during_trade_and_build_play_mamo(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_mamo_phase(
        app, phase=actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO
    )
    game = repository.retrieve(game_id).game
    game.players[other].resources[entities.ResourceCard.WOOD] = 3
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards/mamo",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 200, response.text
    assert response.json()[entities.ResourceCard.WOOD.value] == 3

    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 0


def _setup_mamo_phase(
    app: fastapi.FastAPI,
    phase: actions.GamePhaseName = actions.GamePhaseName.DICE_PLAY_MAMO,
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
    game.players[active_player].cards[entities.WisdomCard.WINDOM_OF_MAMO] = 1
    game_id = repository.add(
        game, phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    )
    repository.update(
        game_id,
        game,
        phase,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other


def _create_game() -> entities.ActiveGame:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
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
