import collections
import datetime

import pytest

from src.game import entities, repository, services


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


def test_active_game_exists_after_all_players_joined(
    repository_: repository.InMemoryRepository,
):
    game_id = repository_.add(
        num_players=3,
        map=[],
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    for i in range(3):
        services.add_player(
            game_id=game_id, username=f"srcolinas-{i}", repository=repository_
        )

    assert repository_.retrieve(game_id) == entities.ActiveGame(
        map=[],
        players={
            "srcolinas-0": entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=[],
                paths=[],
            ),
            "srcolinas-1": entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=[],
                paths=[],
            ),
            "srcolinas-2": entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=[],
                paths=[],
            ),
        },
    )


@pytest.fixture
def repository_() -> repository.InMemoryRepository:
    return repository.InMemoryRepository()
