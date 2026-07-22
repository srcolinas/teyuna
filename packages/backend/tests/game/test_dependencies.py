from src.game import dependencies, repository as repository_module


def test_get_repository_returns_in_memory_repository() -> None:
    dependencies.get_repository.cache_clear()
    try:
        repository = dependencies.get_repository()
        assert isinstance(repository, repository_module.InMemoryGameRepository)
        assert dependencies.get_repository() is repository
    finally:
        dependencies.get_repository.cache_clear()
