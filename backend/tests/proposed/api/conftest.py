from collections.abc import Generator
from typing import Any

import fastapi
import fastapi.testclient as testclient
import pytest

from src import main
from src.active import dependencies, entities, services
from src.active.services import phases


class _StubFirstNode(phases.GamePhaseNode[None, None, None]):
    def run(
        self, game: entities.ActiveGame, request: phases.PlayerRequest
    ) -> phases.RunOutcome[None]:
        return phases.RunOutcome(finished=False, value=None)

    def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
        return phases.ExitOutcome(next=phases.GamePhaseName.FIRST_PLACEMENT, value=None)

    def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
        return phases.EnterOutcome(value=None)


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
