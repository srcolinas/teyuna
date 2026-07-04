from typing import cast

from src.game import entities, ports, repository, services

from . import utils


def test_game_id(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert game.id == game_id


def test_map(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)
    entity_game = cast(entities.ActiveGame, repository_.retrieve(game_id))

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert game.map == entity_game.map


def test_conquistator_location(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)
    entity_game = cast(entities.ActiveGame, repository_.retrieve(game_id))

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert game.conquistator_location == entity_game.conquistator_location
    deserts = [
        hex.coordinate for hex in entity_game.map if hex.type == entities.HexType.DESERT
    ]
    assert game.conquistator_location in deserts


def test_players(
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

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert len(game.players) == 3
    expected = [
        ports.Player(
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
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert game.settlements == []


def test_paths(
    repository_: repository.InMemoryRepository,
) -> None:
    game_id = utils.create_game_and_add_players(repository_=repository_)

    game = services.retrieve_game(game_id, repository=repository_)

    assert game is not None
    assert game.paths == []
