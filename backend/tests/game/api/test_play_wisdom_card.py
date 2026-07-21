import collections
import uuid

import fastapi
import fastapi.testclient as testclient
import pytest

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
        f"/games/{uuid.uuid4()}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1
    game.phase = entities.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    app.dependency_overrides[game_dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 501, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    other = game.turn_order[1]
    game.players[other].cards[entities.WisdomCard.WARRIOR] = 1
    game.phase = entities.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(other)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 403, response.text


def test_returns_400_when_player_does_not_have_card(
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
        f"/games/{game_id}/wisdom-cards",
        json={"card": entities.WisdomCard.WARRIOR.value},
    )

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            entities.WisdomCard.WARRIOR,
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
        ),
        (
            entities.WisdomCard.WINDOM_OF_MAMO,
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        ),
        (
            entities.WisdomCard.BLESSING_OF_ALUNA,
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
        ),
        (
            entities.WisdomCard.PATHFINDER,
            entities.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
        ),
        (
            entities.WisdomCard.LEGACY_OF_THE_ELDERS,
            entities.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_plays_card_during_trade_and_build(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
    card: entities.WisdomCard,
    expected_phase: entities.GamePhaseName,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[card] = 1
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    client.cookies.set("session-token", token)
    response = client.post(
        f"/games/{game_id}/wisdom-cards",
        json={"card": card.value},
    )

    assert response.status_code == 200, response.text
    assert response.json() == expected_phase.value
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is expected_phase
    assert game.players[game.active_player].cards[card] == 0
    assert game.players[game.active_player].played_cards[card] == 1


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
