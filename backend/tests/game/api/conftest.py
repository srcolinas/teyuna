from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src import main
from src.game import dependencies
from src.game import repository


@pytest.fixture
def app() -> fastapi.FastAPI:
    return main.create_app()


@pytest.fixture
def game_repository() -> repository.InMemoryGameRepository:
    return repository.InMemoryGameRepository()


@pytest.fixture
def client(
    app: fastapi.FastAPI,
    game_repository: repository.InMemoryGameRepository,
) -> Generator[testclient.TestClient, Any, None]:
    app.dependency_overrides[dependencies.get_repository] = lambda: game_repository
    with testclient.TestClient(app) as client_:
        yield client_
    app.dependency_overrides.clear()
