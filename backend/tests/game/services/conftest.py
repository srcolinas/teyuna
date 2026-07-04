import pytest

from src.game import repository


@pytest.fixture
def repository_() -> repository.InMemoryRepository:
    return repository.InMemoryRepository()
