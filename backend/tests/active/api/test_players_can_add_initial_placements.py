import collections
import dataclasses
import uuid

import fastapi
import fastapi.testclient as testclient

from src import active, player
from src.active import actions, entities, repository as repository_module

from . import utils


_VALID_TERRACE = (0, -1, 2)
_VALID_PATH = (0, -1, 2)
_INVALID_PATH = (1, 1, 1)


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        uuid.uuid4(),
        tokens[active_player],
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 404, response.text


def test_returns_200_when_active_player_places(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 200, response.text
    settlement, path = response.json()
    assert settlement == {
        "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
        "type": "terrace",
        "owner": active_player,
    }
    assert path == {
        "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
        "owner": active_player,
    }


def test_persists_placement_after_success(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/active-games/{game_id}/settlements")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
            "type": "terrace",
            "owner": active_player,
        }
    ]

    response = client.get(f"/active-games/{game_id}/paths")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "location": {"hex_coord": {"q": 0, "r": -1}, "direction": 2},
            "owner": active_player,
        }
    ]


def test_returns_403_when_player_not_in_turn(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    turn_order = response.json()["turn_order"]
    player_not_in_turn = turn_order[1]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[player_not_in_turn],
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 403, response.text


def test_returns_400_for_invalid_terrace(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    target = entities.canonical_vertex(0, -1, 2)
    adjacent_terrace = entities.canonical_vertex(target.q, target.r, (target.d + 1) % 6)
    game.use_vertex(
        game.active_player, adjacent_terrace, entities.SettlementType.TERRACE
    )
    game_id = repository.add(game)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    token = player.service().add(game.active_player)

    response = utils.post_initial_placements(
        client,
        game_id,
        token,
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_400_for_invalid_path(client: testclient.TestClient) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_initial_placement_payload(_VALID_TERRACE, _INVALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_action_not_allowed(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    response = client.get(f"/active-games/{game_id}")
    active_player = response.json()["turn_order"][0]
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        _registry_with_wrong_action
    )

    response = utils.post_initial_placements(
        client,
        game_id,
        tokens[active_player],
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository = repository_module.InMemoryActiveGameRepository()
    game = _create_game()
    game_id = repository.add(game)
    app.dependency_overrides[active.dependencies.get_repository] = lambda: repository
    app.dependency_overrides[active.dependencies.get_actions_registry] = (
        lambda: actions.ActionsRegistry()
    )
    token = player.service().add(game.active_player)

    response = utils.post_initial_placements(
        client,
        game_id,
        token,
        utils.build_initial_placement_payload(_VALID_TERRACE, _VALID_PATH),
    )

    assert response.status_code == 501, response.text


@dataclasses.dataclass(frozen=True, slots=True)
class _DummyAction(actions.PlayerAction):
    pass


def _registry_with_wrong_action() -> actions.ActionsRegistry:
    registry = actions.ActionsRegistry()

    def handle_dummy(
        game: entities.ActiveGame, action: _DummyAction
    ) -> actions.GamePhaseName:
        return actions.GamePhaseName.DICE_ROLL

    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)
    return registry


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
