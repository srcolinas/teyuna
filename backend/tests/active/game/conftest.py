import pytest
from src.active import entities


@pytest.fixture
def game() -> entities.ActiveGame:
    return entities.ActiveGame.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
