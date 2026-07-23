import collections
import datetime
import uuid

import fastapi
import fastapi.testclient as testclient

from src.game import actions, dependencies as game_dependencies
from src.game import entities, player
from src.game import repository as repository_module
import teyuna_shared


def test_returns_404_when_game_does_not_exist(
    client: testclient.TestClient,
) -> None:
    token = player.service().add("srcolinas-0")
    response = client.post(
        f"/games/{uuid.uuid4()}/discard",
        json={"count": {"wood": 4}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text


def test_returns_400_when_player_not_required_to_discard(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, player_nick, other = _setup_discard_phase(app)
    game = repository.retrieve(game_id)
    game.to_discard_resources = {other: 4}
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/discard",
        json={"count": {"wood": 4}},
        headers={"Authorization": f"Bearer {tokens[player_nick]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_400_when_discard_count_is_wrong(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, player_nick, _ = _setup_discard_phase(app)
    game = repository.retrieve(game_id)
    game.to_discard_resources = {player_nick: 4}
    game.players[player_nick].resources = collections.Counter(
        {teyuna_shared.ResourceCard.WOOD: 9}
    )
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/discard",
        json={"count": {"wood": 5}},
        headers={"Authorization": f"Bearer {tokens[player_nick]}"},
    )

    assert response.status_code == 400, response.text


def test_returns_501_when_phase_not_implemented(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, player_nick, _ = _setup_discard_phase(app)
    app.dependency_overrides[game_dependencies.get_actions_registry] = lambda: (
        actions.ActionsRegistry()
    )

    response = client.post(
        f"/games/{game_id}/discard",
        json={"count": {"wood": 4}},
        headers={"Authorization": f"Bearer {tokens[player_nick]}"},
    )

    assert response.status_code == 501, response.text


def test_discards_and_stays_in_phase_when_others_remain(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, player_nick, other = _setup_discard_phase(app)
    game = repository.retrieve(game_id)
    game.to_discard_resources = {player_nick: 4, other: 5}
    game.players[player_nick].resources = collections.Counter(
        {teyuna_shared.ResourceCard.WOOD: 8}
    )
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/discard",
        json={"count": {"wood": 4}},
        headers={"Authorization": f"Bearer {tokens[player_nick]}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == teyuna_shared.GamePhaseName.DISCARD_RESOURCES.value
    game = repository.retrieve(game_id)
    assert game.to_discard_resources == {other: 5}
    assert game.players[player_nick].resources[teyuna_shared.ResourceCard.WOOD] == 4


def test_last_discard_moves_to_move_conquistator(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, tokens, player_nick, _ = _setup_discard_phase(app)
    game = repository.retrieve(game_id)
    game.to_discard_resources = {player_nick: 4}
    game.players[player_nick].resources = collections.Counter(
        {
            teyuna_shared.ResourceCard.WOOD: 5,
            teyuna_shared.ResourceCard.GOLD: 4,
        }
    )
    repository.update(game_id, game)

    response = client.post(
        f"/games/{game_id}/discard",
        json={"count": {"wood": 2, "gold": 2}},
        headers={"Authorization": f"Bearer {tokens[player_nick]}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == teyuna_shared.GamePhaseName.MOVE_CONQUISTATOR.value
    game = repository.retrieve(game_id)
    assert game.to_discard_resources == {}
    assert sum(game.players[player_nick].resources.values()) == 5


def test_get_game_includes_to_discard_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    repository, game_id, _, player_nick, other = _setup_discard_phase(app)
    game = repository.retrieve(game_id)
    game.to_discard_resources = {player_nick: 4, other: 3}
    repository.update(game_id, game)

    response = client.get(f"/games/{game_id}")

    assert response.status_code == 200, response.text
    assert response.json()["to_discard_resources"] == {
        player_nick: 4,
        other: 3,
    }


def _setup_discard_phase(
    app: fastapi.FastAPI,
) -> tuple[
    repository_module.InMemoryGameRepository,
    uuid.UUID,
    dict[str, str],
    str,
    str,
]:
    repository = repository_module.InMemoryGameRepository()
    game = _create_game()
    player_nick = game.turn_order[0]
    other = game.turn_order[1]
    game.to_discard_resources = {player_nick: 4}
    game.players[player_nick].resources = collections.Counter(
        {teyuna_shared.ResourceCard.WOOD: 8}
    )
    game.phase = teyuna_shared.GamePhaseName.DISCARD_RESOURCES
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game_id = repository.add(game)
    app.dependency_overrides[game_dependencies.get_repository] = lambda: repository
    tokens = {nickname: player.service().add(nickname) for nickname in game.turn_order}
    return repository, game_id, tokens, player_nick, other


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
