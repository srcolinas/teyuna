from typing import cast

from src import active
from src.active import _entities, _ports
from tests import utils


def test_game_id(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert game.id == game_id


def test_map(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)
    entity_game = cast(active.ActiveGame, repository.retrieve(game_id))

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert game.map == entity_game.map


def test_conquistator_location(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)
    entity_game = cast(active.ActiveGame, repository.retrieve(game_id))

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert game.conquistator_location == entity_game.conquistator_location
    deserts = [
        hex.coordinate
        for hex in entity_game.map
        if hex.type == _entities.HexType.DESERT
    ]
    assert game.conquistator_location in deserts


def test_players(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(
        active_repository=repository,
        usernames=[
            "srcolinas-0",
            "srcolinas-1",
            "srcolinas-2",
        ],
    )

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert len(game.players) == 3
    expected = [
        _ports.Player(
            username=f"srcolinas-{i}",
            played_wisdom_cards=[],
            num_hidden_wisdom_cards=0,
            num_resources=0,
            available_settlements=[],
            available_paths=15,
        )
        for i in range(3)
    ]
    assert sorted(game.players, key=lambda p: p.username) == sorted(
        expected, key=lambda p: p.username
    )


def test_settlements(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert game.settlements == []


def test_paths(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert game.paths == []
