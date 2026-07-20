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

    response = client.post(f"/active-games/{uuid.uuid4()}/trades/{uuid.uuid4()}/accept")

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _, accepts, proposal_id = _setup_with_proposal(app)
    game = repository.retrieve(game_id).game
    repository.update(
        game_id,
        game,
        actions.GamePhaseName.FIRST_PLACEMENT,
        phase_deadline=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )

    client.cookies.set("session-token", tokens[accepts])
    response = client.post(f"/active-games/{game_id}/trades/{proposal_id}/accept")

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, accepts, proposal_id = _setup_with_proposal(app)
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )

    client.cookies.set("session-token", tokens[accepts])
    response = client.post(f"/active-games/{game_id}/trades/{proposal_id}/accept")

    assert response.status_code == 501, response.text


def test_returns_400_when_proposal_not_found(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, _, accepts, _ = _setup_with_proposal(app)

    client.cookies.set("session-token", tokens[accepts])
    response = client.post(f"/active-games/{game_id}/trades/{uuid.uuid4()}/accept")

    assert response.status_code == 400, response.text


def test_returns_400_when_not_addressed_to_player(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _, _, proposal_id = _setup_with_proposal(app)
    outsider = repository.retrieve(game_id).game.turn_order[2]

    client.cookies.set("session-token", tokens[outsider])
    response = client.post(f"/active-games/{game_id}/trades/{proposal_id}/accept")

    assert response.status_code == 400, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _, accepts, proposal_id = _setup_with_proposal(
        app, grant_request=False
    )

    client.cookies.set("session-token", tokens[accepts])
    response = client.post(f"/active-games/{game_id}/trades/{proposal_id}/accept")

    assert response.status_code == 400, response.text


def test_accepts_trade(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, proposes, accepts, proposal_id = _setup_with_proposal(
        app
    )

    client.cookies.set("session-token", tokens[accepts])
    response = client.post(f"/active-games/{game_id}/trades/{proposal_id}/accept")

    assert response.status_code == 200, response.text
    assert response.json() == actions.GamePhaseName.TRADE_AND_BUILD.value
    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    assert phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert game.trade_proposals == {}
    assert game.players[proposes].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[proposes].resources[entities.ResourceCard.STONE] == 1
    assert game.players[accepts].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[accepts].resources[entities.ResourceCard.STONE] == 0


def _setup_with_proposal(
    app: fastapi.FastAPI,
    *,
    grant_request: bool = True,
) -> tuple[
    repository_module.InMemoryActiveGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    uuid.UUID,
]:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    proposes = game.active_player
    accepts = game.turn_order[1]
    proposal_id = uuid.uuid4()
    game.players[proposes].resources.update({entities.ResourceCard.GOLD: 1})
    if grant_request:
        game.players[accepts].resources.update({entities.ResourceCard.STONE: 1})
    game.trade_proposals[proposal_id] = entities.TradeProposal(
        by=proposes,
        offer=collections.Counter({entities.ResourceCard.GOLD: 1}),
        request=collections.Counter({entities.ResourceCard.STONE: 1}),
        to={accepts},
    )
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
    return repository, game_id, tokens, proposes, accepts, proposal_id


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
