import collections
import datetime
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


def _coord(vertex: teyuna_core.Coordinate) -> dict[str, int]:
    return {"q": vertex.q, "r": vertex.r, "d": vertex.d}


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    terrace = teyuna_core.canonical_vertex(0, 0, 0)

    response = utils.post_action(
        client,
        uuid.uuid4(),
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=token,
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_player_not_in_turn(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, _, other, terrace = _setup_trade_and_build(app)

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=tokens[other],
    )

    assert response.status_code == 400, response.text


def test_builds_terrace_and_returns_settlement(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, terrace = _setup_trade_and_build(app)

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=tokens[active_player],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "built_settlement"
    assert body["action"]["kind"] == "build_settlement"
    assert body["item"] == teyuna_core.SettlementType.TERRACE.value
    assert body["coordinate"] == [terrace.q, terrace.r, terrace.d]
    game = repository.retrieve(game_id)
    phase = game.phase
    assert phase is teyuna_core.GamePhaseName.TRADE_AND_BUILD
    assert (
        game.players[active_player].settlements[terrace]
        is teyuna_core.SettlementType.TERRACE
    )


def test_returns_400_when_insufficient_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[game.active_player].paths.add(path)
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=token,
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, terrace = _setup_trade_and_build(app)
    game = repository.retrieve(game_id)
    game.phase = teyuna_core.GamePhaseName.DICE_ROLL
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    repository.update(game_id, game)

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=tokens[active_player],
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, active_player, _, terrace = _setup_trade_and_build(app)
    app.dependency_overrides[dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=tokens[active_player],
    )

    assert response.status_code == 501, response.text


def test_returns_400_when_invalid_settlement_location(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[game.active_player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_action(
        client,
        game_id,
        {
            "kind": "build_settlement",
            "item": teyuna_core.SettlementType.TERRACE.value,
            "coordinate": _coord(terrace),
        },
        token=token,
    )

    assert response.status_code == 400, response.text


def test_returns_settlement_by_coordinate(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    game.players[game.active_player].settlements[terrace] = (
        teyuna_core.SettlementType.TERRACE
    )
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository

    response = client.get(
        f"/games/{game_id}/settlements/{terrace.q}/{terrace.r}/{terrace.d}"
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["owner"] == game.active_player
    assert body["type"] == teyuna_core.SettlementType.TERRACE.value


def _setup_trade_and_build(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
    teyuna_core.Coordinate,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    active_player = game.active_player
    other = game.turn_order[1]
    terrace = teyuna_core.canonical_vertex(0, 0, 0)
    path = next(
        iter(teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d))
    )
    game.players[active_player].paths.add(path)
    game.players[active_player].resources.update(
        {
            teyuna_core.ResourceCard.STONE: 1,
            teyuna_core.ResourceCard.WOOD: 1,
            teyuna_core.ResourceCard.COTTON: 1,
            teyuna_core.ResourceCard.MAIZE: 1,
        }
    )
    game.phase = teyuna_core.GamePhaseName.TRADE_AND_BUILD
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    tokens = {
        active_player: player.service().add(active_player),
        other: player.service().add(other),
    }
    return repository, game_id, tokens, active_player, other, terrace


def _create_game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=2
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
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    return game
