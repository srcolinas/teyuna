import collections
import uuid

import fastapi
import fastapi.testclient as testclient
import pytest

from src import active, player
from src.active import actions, entities, repository as repository_module


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)

    response = client.post(
        f"/active-games/{uuid.uuid4()}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.FIRST_PLACEMENT)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
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
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 501, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    other = game.turn_order[1]
    game.players[other].cards[entities.WisdomCard.WARRIOR] = 1
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.DICE_ROLL)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(other)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 403, response.text


def test_returns_400_when_player_does_not_have_card(
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
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            entities.WisdomCard.WARRIOR,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
        ),
        (
            entities.WisdomCard.WINDOM_OF_MAMO,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        ),
        (
            entities.WisdomCard.BLESSING_OF_ALUNA,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
        ),
        (
            entities.WisdomCard.PATHFINDER,
            actions.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
        ),
        (
            entities.WisdomCard.LEGACY_OF_THE_ELDERS,
            actions.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_plays_card_during_trade_and_build(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
    card: entities.WisdomCard,
    expected_phase: actions.GamePhaseName,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[card] = 1
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/active-games/{game_id}/wisdom-cards",
        json={"card": card.value},
    )

    assert response.status_code == 200, response.text
    assert response.json() == expected_phase.value
    game, phase = repository.retrieve(game_id)
    assert phase is expected_phase
    assert game.players[game.active_player].cards[card] == 0
    assert game.players[game.active_player].played_cards[card] == 1


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
