import collections
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import entities, dependencies as game_dependencies
from src.game import player
from src.game import actions, repository as repository_module

from . import utils
import datetime
import teyuna_shared


_VALID_TERRACE = (0, -1, 2)
_VALID_PATH = (0, -1, 2)
_INVALID_PATH = (1, 1, 1)


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        uuid.uuid4(),
        tokens[active_player],
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 404, response.text


def test_returns_200_when_active_player_places(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "placed_buildings"
    assert body["action"]["kind"] == "free_placement"
    assert body["settlement"] == [0, -1, 2]
    assert body["path"] == [0, -1, 2]


def test_persists_placement_after_success(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/settlements")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
            "type": "terrace",
            "owner": active_player,
        }
    ]

    response = client.get(f"/games/{game_id}/paths")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
            "owner": active_player,
        }
    ]


def test_returns_400_when_player_not_in_turn(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    turn_order = response.json()["turn_order"]
    player_not_in_turn = turn_order[1]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[player_not_in_turn],
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_400_for_invalid_terrace(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    target = teyuna_shared.canonical_vertex(0, -1, 2)
    adjacent_terrace = teyuna_shared.canonical_vertex(
        target.q, target.r, (target.d + 1) % 6
    )
    game.use_vertex(
        game.active_player, adjacent_terrace, teyuna_shared.SettlementType.TERRACE
    )
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_initial_placements(
        client,
        game_id,
        token,
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_400_for_invalid_path(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_free_placement_action(_VALID_TERRACE, _INVALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_200_when_payload_is_empty(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "placed_buildings"
    assert body["action"]["kind"] == "free_placement"
    assert body["settlement"] is not None
    assert body["path"] is not None
    assert len(body["settlement"]) == 3
    assert len(body["path"]) == 3

    response = client.get(f"/games/{game_id}/settlements")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]["owner"] == active_player

    response = client.get(f"/games/{game_id}/paths")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]["owner"] == active_player


def test_returns_200_when_only_terrace_provided(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_free_placement_action(terrace=_VALID_TERRACE),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "placed_buildings"
    assert body["settlement"] == [0, -1, 2]
    assert body["path"] is not None
    assert len(body["path"]) == 3


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/games/{game_id}")
    active_player = response.json()["turn_order"][0]
    app.dependency_overrides[game_dependencies.get_actions_registry] = (
        _registry_with_wrong_action
    )

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    response = utils.post_initial_placements(
        client,
        game_id,
        token,
        utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 501, response.text


class _DummyAction(teyuna_shared.PlayerAction):
    pass


def _registry_with_wrong_action() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()

    def handle_dummy(
        game: entities.Game, action: _DummyAction
    ) -> teyuna_shared.ActionExecutionResult:
        return teyuna_shared.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=teyuna_shared.GamePhaseName.DICE_ROLL,
            action=action,
        )

    registry.register(teyuna_shared.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)
    return registry


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
