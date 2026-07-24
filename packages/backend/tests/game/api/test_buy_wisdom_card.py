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


_WISDOM_CARD_COST = {
    teyuna_core.ResourceCard.GOLD: 1,
    teyuna_core.ResourceCard.COTTON: 1,
    teyuna_core.ResourceCard.MAIZE: 1,
}


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")

    response = utils.post_action(
        client,
        uuid.uuid4(),
        {"kind": "buy_wisdom_card"},
        token=token,
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[active_player],
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    app.dependency_overrides[dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[active_player],
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, _ = _setup_trade_and_build(app)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[other],
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(
        app, grant_cost=False
    )
    game = repository.retrieve(game_id)
    game.players[active_player].resources.update(
        {
            teyuna_core.ResourceCard.GOLD: 1,
            teyuna_core.ResourceCard.COTTON: 0,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[active_player],
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_deck_is_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.wisdom_deck = []
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[active_player],
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Cannot buy more wisdom cards"


def test_buys_wisdom_card(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, card = _setup_trade_and_build(app)

    response = utils.post_action(
        client,
        game_id,
        {"kind": "buy_wisdom_card"},
        token=tokens[active_player],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"]["kind"] == "buy_wisdom_card"
    assert body["next_phase"] == teyuna_core.GamePhaseName.TRADE_AND_BUILD.value
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert game.wisdom_deck == []
    assert game.players[active_player].cards_bought_this_turn[card] == 1
    assert game.players[active_player].cards[card] == 0
    for resource in _WISDOM_CARD_COST:
        assert game.players[active_player].resources[resource] == 0


def _setup_trade_and_build(
    app: fastapi.FastAPI,
    *,
    grant_cost: bool = True,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    teyuna_core.WisdomCard,
]:
    repository = repository_module.InMemoryGameRepository()
    card = teyuna_core.WisdomCard.WARRIOR
    game = _create_game(card)
    active_player = game.active_player
    other = game.turn_order[1]
    if grant_cost:
        game.players[active_player].resources.update(_WISDOM_CARD_COST)
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player, other, card


def _create_game(top_card: teyuna_core.WisdomCard) -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
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
            for nickname in ("srcolinas-0", "srcolinas-1", "srcolinas-2")
        },
        wisdom_deck=[top_card],
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    return game
