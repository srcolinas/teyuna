import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src import active, player
from src.active import actions, entities, repository as repository_module


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

    response = client.post(f"/active-games/{uuid.uuid4()}/wisdom-cards/buy")

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game, _ = repository.retrieve(game_id)
    repository.update(game_id, game, actions.GamePhaseName.FIRST_PLACEMENT)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 501, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, other, _ = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[other])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 403, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(
        app, grant_cost=False
    )
    game, _ = repository.retrieve(game_id)
    game.players[active_player].resources.update(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        }
    )
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text


def test_returns_400_when_deck_is_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, _ = _setup_trade_and_build(app)
    game, _ = repository.retrieve(game_id)
    game.wisdom_deck = []
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Cannot buy more wisdom cards"


def test_buys_wisdom_card(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, card = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(f"/active-games/{game_id}/wisdom-cards/buy")

    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.TRADE_AND_BUILD.value
    game, phase = repository.retrieve(game_id)
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
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
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    entities.WisdomCard,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    card = entities.WisdomCard.WARRIOR
    game = _create_game(card)
    active_player = game.active_player
    other = game.turn_order[1]
    if grant_cost:
        game.players[active_player].resources.update(_WISDOM_CARD_COST)
    game_id = repository.add(game)
    repository.update(game_id, game, actions.GamePhaseName.TRADE_AND_BUILD)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player, other, card


def _create_game(top_card: entities.WisdomCard) -> entities.ActiveGame:
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
        wisdom_deck=[top_card],
    )
