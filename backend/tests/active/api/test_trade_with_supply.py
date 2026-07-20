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
        f"/active-games/{uuid.uuid4()}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player = _setup_trade_and_build(app)
    game = repository.retrieve(game_id).game
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.FIRST_PLACEMENT,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player = _setup_trade_and_build(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 501, response.text


def test_returns_403_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _ = _setup_trade_and_build(app)
    other = repository.retrieve(game_id).game.turn_order[1]
    game = repository.retrieve(game_id).game
    game.players[other].resources.update({entities.ResourceCard.GOLD: 4})
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 403, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player = _setup_trade_and_build(app, grant_offer=False)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_supply_is_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player = _setup_trade_and_build(app)
    game = repository.retrieve(game_id).game
    game.resource_supply[entities.ResourceCard.STONE] = 0
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_trades_with_supply_at_default_rate(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.TRADE_AND_BUILD.value
    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.players[active_player].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[active_player].resources[entities.ResourceCard.STONE] == 1


def _setup_trade_and_build(
    app: fastapi.FastAPI,
    *,
    grant_offer: bool = True,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    active_player = game.active_player
    if grant_offer:
        game.players[active_player].resources.update({entities.ResourceCard.GOLD: 4})
    game_id = repository.add(
        game, phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    )
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player


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
