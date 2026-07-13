import pytest

from src.active import entities, services
from src.active.services import phases


def test_game_id(manager: services.GameManager) -> None:
    game_id = manager.create_game(["srcolinas-1", "srcolinas-2"])
    game = manager.retrieve(game_id)
    assert game.id == game_id


def test_turn_order(manager: services.GameManager) -> None:
    game_id = manager.create_game(["srcolinas-3", "srcolinas-2", "srcolinas-1"])
    game = manager.retrieve(game_id)
    assert game is not None
    assert sorted(game.turn_order) == ["srcolinas-1", "srcolinas-2", "srcolinas-3"]


@pytest.fixture
def manager() -> services.GameManager:
    class FirstNode(phases.GamePhaseNode):
        def run(self, game: entities.ActiveGame, request: phases.PlayerRequest) -> bool:
            return False

        def on_exit(self, game: entities.ActiveGame) -> phases.GamePhaseName:
            return phases.GamePhaseName.FIRST_PLACEMENT

    return services.GameManager({phases.GamePhaseName.FIRST_PLACEMENT: FirstNode()})
