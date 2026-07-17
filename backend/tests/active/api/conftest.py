from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src import main


@pytest.fixture
def app() -> fastapi.FastAPI:
    return main.create_app()


@pytest.fixture
def client(app: fastapi.FastAPI) -> Generator[testclient.TestClient, Any, None]:
    with testclient.TestClient(app) as client_:
        yield client_
    app.dependency_overrides.clear()
