from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src import main
from src.active import dependencies, entities, services
from src.active.services import phases


class _StubFirstNode(phases.GamePhaseNode):
    def run(self, game: entities.ActiveGame, request: phases.PlayerRequest) -> bool:
        return False

    def on_exit(self, game: entities.ActiveGame) -> phases.GamePhaseName:
        return phases.GamePhaseName.FIRST_PLACEMENT


@pytest.fixture
def app() -> fastapi.FastAPI:
    application = main.create_app()
    manager = services.GameManager(
        {phases.GamePhaseName.FIRST_PLACEMENT: _StubFirstNode()}
    )
    application.dependency_overrides[dependencies.get_game_manager] = lambda: manager
    return application


@pytest.fixture
def client(app: fastapi.FastAPI) -> Generator[testclient.TestClient, Any, None]:
    client_ = testclient.TestClient(app)
    yield client_
    app.dependency_overrides.clear()
