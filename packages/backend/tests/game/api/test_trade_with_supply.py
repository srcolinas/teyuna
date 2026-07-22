import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module
import datetime
import teyuna_shared


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    client.cookies.set("session-token", token)

    response = client.post(
        f"/games/{uuid.uuid4()}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player = _setup_trade_and_build(app)
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _ = _setup_trade_and_build(app)
    other = repository.retrieve(game_id).turn_order[1]
    game = repository.retrieve(game_id)
    game.players[other].resources.update({teyuna_shared.ResourceCard.GOLD: 4})
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player = _setup_trade_and_build(app, grant_offer=False)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_supply_is_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.resource_supply[teyuna_shared.ResourceCard.STONE] = 0
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/games/{game_id}/trades/supply",
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
        f"/games/{game_id}/trades/supply",
        json={"offers": "gold", "requests": "stone"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == teyuna_shared.GamePhaseName.TRADE_AND_BUILD.value
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert game.players[active_player].resources[teyuna_shared.ResourceCard.GOLD] == 0
    assert game.players[active_player].resources[teyuna_shared.ResourceCard.STONE] == 1


def _setup_trade_and_build(
    app: fastapi.FastAPI,
    *,
    grant_offer: bool = True,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    if grant_offer:
        game.players[active_player].resources.update(
            {teyuna_shared.ResourceCard.GOLD: 4}
        )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player


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
