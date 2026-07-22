import collections

import fastapi
import fastapi.testclient as testclient
import teyuna_shared

from src.game import dependencies, repository as repository_module

from . import utils


def test_returns_401_without_session_cookie(client: testclient.TestClient) -> None:
    game_id = utils.create_active_game(client)
    client.cookies.clear()

    response = client.get(f"/games/{game_id}/hand")

    assert response.status_code == 401


def test_returns_401_with_invalid_session_cookie(
    client: testclient.TestClient,
) -> None:
    game_id = utils.create_active_game(client)
    client.cookies.set("session-token", "not-a-real-token")

    response = client.get(f"/games/{game_id}/hand")

    assert response.status_code == 401


def test_returns_private_hand_for_authenticated_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    game_id, tokens = utils.create_active_game_with_tokens(client)
    nickname = next(iter(tokens))
    token = tokens[nickname]

    game = repository.retrieve(game_id)
    game.players[nickname].resources = collections.Counter(
        {
            teyuna_shared.ResourceCard.GOLD: 2,
            teyuna_shared.ResourceCard.WOOD: 1,
            teyuna_shared.ResourceCard.STONE: 0,
            teyuna_shared.ResourceCard.COTTON: 0,
            teyuna_shared.ResourceCard.MAIZE: 3,
        }
    )
    game.players[nickname].cards = collections.Counter(
        {teyuna_shared.WisdomCard.WARRIOR: 1}
    )
    game.players[nickname].cards_bought_this_turn = collections.Counter(
        {teyuna_shared.WisdomCard.PATHFINDER: 1}
    )

    client.cookies.set("session-token", token)
    response = client.get(f"/games/{game_id}/hand")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["resources"] == {
        "gold": 2,
        "wood": 1,
        "stone": 0,
        "cotton": 0,
        "maize": 3,
    }
    assert sorted(body["wisdom_cards"]) == sorted(["warrior", "pathfinder"])


def test_public_player_view_does_not_expose_hand(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    game_id, tokens = utils.create_active_game_with_tokens(client)
    nickname = next(iter(tokens))

    game = repository.retrieve(game_id)
    game.players[nickname].resources = collections.Counter(
        {teyuna_shared.ResourceCard.GOLD: 4}
    )
    game.players[nickname].cards = collections.Counter(
        {teyuna_shared.WisdomCard.WARRIOR: 2}
    )

    response = client.get(f"/games/{game_id}/players/{nickname}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert "resources" not in body
    assert "wisdom_cards" not in body
    assert body["num_resources"] == 4
    assert body["num_hidden_wisdom_cards"] == 2
