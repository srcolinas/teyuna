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

    response = client.post(
        f"/active-games/{uuid.uuid4()}/resources",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_wrong_phase(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_mamo_phase(app)
    repository.update(
        game_id,
        repository.retrieve(game_id)[0],
        actions.GamePhaseName.DICE_ROLL,
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/resources",
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
        f"/active-games/{game_id}/resources",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 403, response.text


def test_mamo_takes_all_of_resource(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_mamo_phase(app)
    game, _ = repository.retrieve(game_id)
    game.players[other].resources[entities.ResourceCard.WOOD] = 3
    repository.update(game_id, game, actions.GamePhaseName.DICE_PLAY_MAMO)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/resources",
        json={"resource": entities.ResourceCard.WOOD.value},
    )

    assert response.status_code == 200, response.text
    assert response.json()[entities.ResourceCard.WOOD.value] == 3

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 0


def test_blessed_takes_two_from_supply(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _ = _setup_blessed_phase(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/resources",
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

    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.DICE_ROLL


def _setup_mamo_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(
        app,
        entities.WisdomCard.WINDOM_OF_MAMO,
        actions.GamePhaseName.DICE_PLAY_MAMO,
    )


def _setup_blessed_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    return _setup_phase(
        app,
        entities.WisdomCard.BLESSING_OF_ALUNA,
        actions.GamePhaseName.DICE_PLAY_BLESSED,
    )


def _setup_phase(
    app: fastapi.FastAPI,
    card: entities.WisdomCard,
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
    game.players[active_player].cards[card] = 1
    game_id = repository.add(game)
    repository.update(game_id, game, phase)
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
