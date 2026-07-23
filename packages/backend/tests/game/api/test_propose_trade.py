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
    response = client.post(
        f"/games/{uuid.uuid4()}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": ["srcolinas-1"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = teyuna_shared.GamePhaseName.FIRST_PLACEMENT
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(
        app, grant_offer=False
    )

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_targets_are_empty(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    _, game_id, tokens, active_player, _ = _setup_trade_and_build(app)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [],
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 400, response.text


def test_proposes_trade(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [other],
        },
        headers={"Authorization": f"Bearer {tokens[active_player]}"},
    )

    assert response.status_code == 200, response.text
    assert (
        teyuna_shared.TradeProposal(
            by=active_player,
            to={other},
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 1}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
        )
        in repository.retrieve(game_id).trade_proposals.values()
    )

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text
    proposals = response.json()["trade_proposals"]
    assert len(proposals) == 1
    assert proposals[0]["by"] == active_player
    assert proposals[0]["to"] == [other]
    assert proposals[0]["offer"] == {"gold": 1}
    assert proposals[0]["request"] == {"stone": 1}
    assert uuid.UUID(proposals[0]["id"]) in repository.retrieve(game_id).trade_proposals


def test_non_active_player_can_propose(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.players[other].resources.update({teyuna_shared.ResourceCard.GOLD: 1})
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [active_player],
        },
        headers={"Authorization": f"Bearer {tokens[other]}"},
    )

    assert response.status_code == 200, response.text
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase == teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    assert (
        teyuna_shared.TradeProposal(
            by=other,
            to={active_player},
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 1}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
        )
        in game.trade_proposals.values()
    )

    response = client.get(f"/games/{game_id}")
    assert response.status_code == 200, response.text
    proposals = response.json()["trade_proposals"]
    assert len(proposals) == 1
    assert proposals[0]["by"] == other
    assert proposals[0]["to"] == [active_player]


def test_non_active_player_can_propose_during_dice_roll(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.players[other].resources.update({teyuna_shared.ResourceCard.GOLD: 1})
    game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [active_player],
        },
        headers={"Authorization": f"Bearer {tokens[other]}"},
    )

    assert response.status_code == 200, response.text
    game = repository.retrieve(game_id)
    assert game.phase is teyuna_shared.GamePhaseName.DICE_ROLL
    assert (
        teyuna_shared.TradeProposal(
            by=other,
            to={active_player},
            offer=collections.Counter({teyuna_shared.ResourceCard.GOLD: 1}),
            request=collections.Counter({teyuna_shared.ResourceCard.STONE: 1}),
        )
        in game.trade_proposals.values()
    )


def test_non_active_player_cannot_propose_to_non_active(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _, other = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    third = game.turn_order[2]
    game.players[other].resources.update({teyuna_shared.ResourceCard.GOLD: 1})
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/trades",
        json={
            "offer": {"gold": 1},
            "request": {"stone": 1},
            "to": [third],
        },
        headers={"Authorization": f"Bearer {tokens[other]}"},
    )

    assert response.status_code == 400, response.text


def _setup_trade_and_build(
    app: fastapi.FastAPI,
    *,
    grant_offer: bool = True,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    if grant_offer:
        game.players[active_player].resources.update(
            {teyuna_shared.ResourceCard.GOLD: 1}
        )
    game.phase = teyuna_shared.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, active_player, other


def _create_game() -> entities.Game:
    mountains = teyuna_shared.MapHex(
        q=0, r=0, type=teyuna_shared.HexType.MOUNTAINS, number=8
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
