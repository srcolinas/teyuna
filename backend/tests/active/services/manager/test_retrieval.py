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
    class FirstNode(phases.GamePhaseNode[None, None, None]):
        def run(
            self, game: entities.ActiveGame, request: phases.PlayerRequest
        ) -> phases.RunOutcome[None]:
            return phases.RunOutcome(finished=False, value=None)

        def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
            return phases.ExitOutcome(
                next=phases.GamePhaseName.FIRST_PLACEMENT, value=None
            )

        def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
            return phases.EnterOutcome(value=None)

    return services.GameManager({phases.GamePhaseName.FIRST_PLACEMENT: FirstNode()})
