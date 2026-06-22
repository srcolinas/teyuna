import datetime

import pytest

from src.game import repository, services


def test_player_can_be_added_before_expiration(
    repository_: repository.InMemoryRepository,
):
    game_id = repository_.add(
        num_players=3,
        map=[],
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    game = services.add_player(
        game_id=game_id, username="srcolinas", repository=repository_
    )
    assert len(game.players) == 1
    assert game.players[0].username == "srcolinas"


def test_player_cannot_be_added_after_expiration(
    repository_: repository.InMemoryRepository,
):
    game_id = repository_.add(
        num_players=3,
        map=[],
        expires_at=datetime.datetime.now() - datetime.timedelta(seconds=100),
    ).id
    with pytest.raises(services.GameExpiredError):
        services.add_player(
            game_id=game_id, username="srcolinas", repository=repository_
        )


@pytest.fixture
def repository_() -> repository.InMemoryRepository:
    return repository.InMemoryRepository()
