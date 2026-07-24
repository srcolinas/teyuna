import uuid

import pytest

from src.game import entities, repository as repository_module
import teyuna_core


def test_items_returns_all_stored_games() -> None:
    repository = repository_module.InMemoryGameRepository()
    game_a = _empty_game()
    game_b = _empty_game()
    id_a = repository.add(game_a)
    id_b = repository.add(game_b)

    items = dict(repository.items())

    assert items == {id_a: game_a, id_b: game_b}


def test_items_returns_empty_when_no_games_stored() -> None:
    repository = repository_module.InMemoryGameRepository()

    assert tuple(repository.items()) == ()


def test_retrieve_raises_when_game_does_not_exist() -> None:
    repository = repository_module.InMemoryGameRepository()

    with pytest.raises(repository_module.GameDoesNotExistError):
        repository.retrieve(uuid.uuid4())


def test_update_raises_when_game_does_not_exist() -> None:
    repository = repository_module.InMemoryGameRepository()

    with pytest.raises(repository_module.GameDoesNotExistError):
        repository.update(uuid.uuid4(), _empty_game())


def _empty_game() -> entities.Game:
    return entities.Game(
        map=(),
        players={},
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=3,
    )
