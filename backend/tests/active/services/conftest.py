import pytest

from src import active
from src.active.services import create_new


@pytest.fixture
def repository() -> active.InMemoryActiveGameRepository:
    return active.InMemoryActiveGameRepository()


@pytest.fixture
def game() -> active.entities.ActiveGame:
    return create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
