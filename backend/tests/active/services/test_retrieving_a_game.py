from src import active

from ... import utils


def test_game_id(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = active.retrieve_game(game_id, repository=repository)
    assert game.id == game_id


def test_map(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)
    entity_game = repository.retrieve(game_id)

    game = active.retrieve_game(game_id, repository=repository)

    assert game.map == entity_game.map


def test_conquistator_location(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)
    entity_game = repository.retrieve(game_id)

    game = active.retrieve_game(game_id, repository=repository)

    assert game.conquistator_location.q == entity_game.conquistator_location.q
    assert game.conquistator_location.r == entity_game.conquistator_location.r


def test_players(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(
        active_repository=repository,
        nicknames=[
            "srcolinas-0",
            "srcolinas-1",
            "srcolinas-2",
        ],
    )

    game = active.retrieve_game(game_id, repository=repository)

    assert game is not None
    assert len(game.players) == 3
    expected = [
        active.ports.Player(
            nickname=f"srcolinas-{i}",
            played_wisdom_cards=[],
            num_hidden_wisdom_cards=0,
            num_resources=0,
            available_teraces=5,
            available_great_teraces=4,
            available_paths=15,
        )
        for i in range(3)
    ]
    assert sorted(game.players, key=lambda p: p.nickname) == sorted(
        expected, key=lambda p: p.nickname
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


def test_turn_order(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(
        active_repository=repository,
        nicknames=["srcolinas-1", "srcolinas-2", "srcolinas-3"],
    )
    game = active.retrieve_game(game_id, repository=repository)
    assert game is not None
    assert sorted(game.turn_order) == ["srcolinas-1", "srcolinas-2", "srcolinas-3"]
