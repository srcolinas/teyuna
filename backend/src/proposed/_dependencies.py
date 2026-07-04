import functools

from . import _repository


@functools.cache
def get_repository() -> _repository.InMemoryProposedGameRepository:
    return _repository.InMemoryProposedGameRepository()
