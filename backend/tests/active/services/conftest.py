import pytest

from src import active


@pytest.fixture
def repository() -> active.InMemoryActiveGameRepository:
    return active.InMemoryActiveGameRepository()
