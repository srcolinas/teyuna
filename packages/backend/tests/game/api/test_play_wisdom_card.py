import collections
import uuid

import fastapi
import fastapi.testclient as testclient
import pytest

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module

from . import utils
import datetime
import teyuna_shared


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")

    response = utils.post_action(
        client,
        uuid.uuid4(),
        {"kind": "play_wisdom_card", "card": teyuna_shared.WisdomCard.WARRIOR.value},
        token=token,
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase = teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "play_wisdom_card", "card": teyuna_shared.WisdomCard.WARRIOR.value},
        token=token,
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[teyuna_shared.WisdomCard.WARRIOR] = 1
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "play_wisdom_card", "card": teyuna_shared.WisdomCard.WARRIOR.value},
        token=token,
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    other = game.turn_order[1]
    game.players[other].cards[teyuna_shared.WisdomCard.WARRIOR] = 1
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(other)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "play_wisdom_card", "card": teyuna_shared.WisdomCard.WARRIOR.value},
        token=token,
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_player_does_not_have_card(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "play_wisdom_card", "card": teyuna_shared.WisdomCard.WARRIOR.value},
        token=token,
    )

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            teyuna_shared.WisdomCard.WARRIOR,
            teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
        ),
        (
            teyuna_shared.WisdomCard.WINDOM_OF_MAMO,
            teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
        ),
        (
            teyuna_shared.WisdomCard.BLESSING_OF_ALUNA,
            teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
        ),
        (
            teyuna_shared.WisdomCard.PATHFINDER,
            teyuna_shared.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
        ),
        (
            teyuna_shared.WisdomCard.LEGACY_OF_THE_ELDERS,
            teyuna_shared.GamePhaseName.TRADE_AND_BUILD,
        ),
    ],
)
def test_plays_card_during_trade_and_build(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
    card: teyuna_shared.WisdomCard,
    expected_phase: teyuna_shared.GamePhaseName,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.players[game.active_player].cards[card] = 1
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "play_wisdom_card", "card": card.value},
        token=token,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"]["kind"] == "play_wisdom_card"
    assert body["next_phase"] == expected_phase.value
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is expected_phase
    assert game.players[game.active_player].cards[card] == 0
    assert game.players[game.active_player].played_cards[card] == 1


def _create_game() -> entities.Game:
    mountains = teyuna_shared.MapHex(
        q=0, r=0, type=teyuna_shared.HexType.MOUNTAINS, number=1
    )
    game = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_shared.HexLocation(q=mountains.q, r=mountains.r),
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
