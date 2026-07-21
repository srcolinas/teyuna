import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import (
    entities,
    dependencies,
    player,
    repository as repository_module,
    actions,
)
import datetime


_WISDOM_CARD_COST = {
    entities.ResourceCard.GOLD: 1,
    entities.ResourceCard.COTTON: 1,
    entities.ResourceCard.MAIZE: 1,
}


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)

    response = client.post(f"/games/{uuid.uuid4()}/wisdom-cards/buy")

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    app.dependency_overrides[dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 501, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, _ = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

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
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text


def test_returns_400_when_deck_is_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.wisdom_deck = []
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Cannot buy more wisdom cards"


def test_buys_wisdom_card(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, card = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 200, response.text
    assert response.json() == entities.GamePhaseName.TRADE_AND_BUILD.value
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is entities.GamePhaseName.TRADE_AND_BUILD
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
    entities.WisdomCard,
]:
    repository = repository_module.InMemoryGameRepository()
    card = entities.WisdomCard.WARRIOR
    game = _create_game(card)
    active_player = game.active_player
    other = game.turn_order[1]
    if grant_cost:
        game.players[active_player].resources.update(_WISDOM_CARD_COST)
    game.phase = entities.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player, other, card


def _create_game(top_card: entities.WisdomCard) -> entities.Game:
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
        wisdom_deck=[top_card],
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    return game
