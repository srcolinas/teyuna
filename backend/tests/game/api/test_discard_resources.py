import collections
import datetime

import fastapi
import fastapi.testclient as testclient
import pydantic
import pytest

from src.game import dependencies, entities, player, routes
from src.game import repository as repository_module


def test_authenticated_player_can_discard_required_resources(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    nickname = "alice"
    game = entities.Game(
        map=(
            entities.Hex(
                q=0,
                r=0,
                type=entities.HexType.MOUNTAINS,
                number=5,
            ),
        ),
        conquistator_location=entities.HexLocation(q=0, r=0),
        players={nickname: entities.Player()},
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    game.phase = entities.GamePhaseName.DISCARD_RESOURCES
    game.phase_deadline = datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC)
    game.to_discard_resources = {nickname: 4}
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 5,
            entities.ResourceCard.WOOD: 3,
        }
    )
    repository = repository_module.InMemoryGameRepository()
    game_id = repository.add(game)
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    client.cookies.set("session-token", player.service().add(nickname))

    response = client.post(
        f"/games/{game_id}/resources/discard",
        json={"count": {"gold": 4}},
    )

    assert response.status_code == 200, response.text
    assert response.json() == entities.GamePhaseName.MOVE_CONQUISTATOR.value
    stored = repository.retrieve(game_id)
    assert stored.players[nickname].resources == collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.WOOD: 3,
        }
    )
    assert stored.to_discard_resources == {}


def test_discard_payload_rejects_negative_resource_amounts() -> None:
    with pytest.raises(pydantic.ValidationError):
        routes.DiscardResourcesPayload(count={entities.ResourceCard.GOLD: -1})
