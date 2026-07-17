from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src import main
from src.proposed import dependencies, repository


@pytest.fixture
def app() -> fastapi.FastAPI:
    return main.create_app()


@pytest.fixture
def proposed_repository() -> repository.InMemoryProposedGameRepository:
    return repository.InMemoryProposedGameRepository()


@pytest.fixture
def client(
    app: fastapi.FastAPI,
    proposed_repository: repository.InMemoryProposedGameRepository,
) -> Generator[testclient.TestClient, Any, None]:
    app.dependency_overrides[dependencies.get_repository] = lambda: proposed_repository
    with testclient.TestClient(app) as client_:
        yield client_
    app.dependency_overrides.clear()
