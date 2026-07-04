import collections
import datetime
from typing import cast

import pytest

from src.game import entities, repository, services

from . import utils


def test_player_can_be_added_before_expiration(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = repository_.add(
        num_players=3,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id
    game = services.add_player(
        game_id=game_id, username="srcolinas", repository=repository_
    )
    assert len(game.players) == 1
    assert list(game.players)[0] == "srcolinas"


def test_player_cannot_be_added_after_expiration(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = repository_.add(
        num_players=3,
        expires_at=datetime.datetime.now() - datetime.timedelta(seconds=100),
    ).id
    with pytest.raises(services.GameExpiredError):
        services.add_player(
            game_id=game_id, username="srcolinas", repository=repository_
        )


def test_active_game_exists_after_all_players_joined(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = repository_.retrieve(game_id)
    assert game is not None


def test_active_game_correctly_initialize_players(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(
        repository_=repository_,
        usernames=[
            "srcolinas-0",
            "srcolinas-1",
            "srcolinas-2",
        ],
    )

    game = cast(entities.ActiveGame, repository_.retrieve(game_id))
    assert len(game.players) == 3
    for i in range(3):
        assert f"srcolinas-{i}" in game.players
        assert game.players[f"srcolinas-{i}"] == entities.Player(
            cards=collections.Counter(),
            played_cards=collections.Counter(),
            resources=collections.Counter(),
            settlements=[],
            paths=[],
        )


def test_map_has_correct_resource_quantities(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = cast(entities.ActiveGame, repository_.retrieve(game_id))
    counts = collections.Counter(hex.type for hex in game.map)
    assert counts == {
        entities.HexType.MOUNTAINS: 3,
        entities.HexType.QUARRIES: 3,
        entities.HexType.HIGHLANDS: 4,
        entities.HexType.VALLEYS: 4,
        entities.HexType.JUNGLE: 4,
        entities.HexType.DESERT: 1,
    }


def test_map_has_correct_number_distribution(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = cast(entities.ActiveGame, repository_.retrieve(game_id))
    counts = collections.Counter(hex.number for hex in game.map)
    assert counts == {
        2: 1,
        3: 2,
        4: 2,
        5: 2,
        6: 2,
        7: 1,
        8: 2,
        9: 2,
        10: 2,
        11: 2,
        12: 1,
    }


def test_conquistator_is_located_in_desert_when_game_starts(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)
    game = cast(entities.ActiveGame, repository_.retrieve(game_id))
    deserts = [
        hex.coordinate for hex in game.map if hex.type == entities.HexType.DESERT
    ]
    assert game.conquistator_location in deserts
