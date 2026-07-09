import functools

from . import repository


@functools.cache
def get_repository() -> repository.InMemoryProposedGameRepository:
    return repository.InMemoryProposedGameRepository()
