import pytest


from src.active import entities, services, repository as repository_module


@pytest.fixture
def repository() -> repository_module.InMemoryActiveGameRepository:
    return repository_module.InMemoryActiveGameRepository()


@pytest.fixture
def game() -> entities.ActiveGame:
    return services.create_new(["srcolinas-1", "srcolinas-2", "srcolinas-3"])
