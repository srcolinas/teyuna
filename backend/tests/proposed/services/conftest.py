import uuid

import pytest

from src.active import _repository as active_repository
from src.active._services import _manager
from src.proposed import _repository as proposed_repository


@pytest.fixture
def repository_() -> proposed_repository.InMemoryProposedGameRepository:
    return proposed_repository.InMemoryProposedGameRepository()


@pytest.fixture
def active_repository_() -> active_repository.InMemoryActiveGameRepository:
    return active_repository.InMemoryActiveGameRepository()


@pytest.fixture
def manager_(
    active_repository_: active_repository.InMemoryActiveGameRepository,
) -> _manager.GameManager:
    return _manager.GameManager(active_repository_)


class _FakeManager:
    def start(self, players: tuple[str, ...]) -> uuid.UUID:
        raise AssertionError("GameManager.start should not be called")


@pytest.fixture
def fake_manager_() -> _FakeManager:
    return _FakeManager()
