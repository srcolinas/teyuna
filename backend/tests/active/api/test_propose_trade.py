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
        f"/active-games/{uuid.uuid4()}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": ["srcolinas-1"],
        },
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id).game
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.FIRST_PLACEMENT,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(
        app, grant_offer=False
    )

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_targets_are_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player, _ = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [],
        },
    )

    assert response.status_code == 400, response.text


def test_non_active_player_can_propose(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id).game
    game.players[other].resources.update({entities.ResourceCard.GOLD: 1})
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.TRADE_AND_BUILD,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[other])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [active_player],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    proposal_id = uuid.UUID(body["id"])
    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert proposal_id in game.trade_proposals
    assert game.trade_proposals[proposal_id].by == other


def test_proposes_trade(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)

    client.cookies.set("session-token", tokens[active_player])
    response = client.post(
        f"/active-games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    proposal_id = uuid.UUID(body["id"])
    game = repository.retrieve(game_id).game
    assert game.trade_proposals[proposal_id].to == {other}
    assert game.players[active_player].resources[entities.ResourceCard.GOLD] == 1


def _setup_trade_and_build(
    app: fastapi.FastAPI,
    *,
    grant_offer: bool = True,
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
    if grant_offer:
        game.players[active_player].resources.update({entities.ResourceCard.GOLD: 1})
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
