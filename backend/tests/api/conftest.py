from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src.main import app as _app


@pytest.fixture
def app() -> fastapi.FastAPI:
    return _app


@pytest.fixture
def client(app: fastapi.FastAPI) -> Generator[testclient.TestClient, Any, None]:
    client_ = testclient.TestClient(app)
    yield client_
    app.dependency_overrides.clear()
