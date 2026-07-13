import pytest

from src.active import entities, services


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
    class FirstNode(services.GamePhaseNode):
        def run(
            self, game: entities.ActiveGame, request: services.PlayerRequest
        ) -> bool:
            return False

        def on_exit(self, game: entities.ActiveGame) -> entities.GamePhaseName:
            return entities.GamePhaseName.FIRST_PLACEMENT

    return services.GameManager({entities.GamePhaseName.FIRST_PLACEMENT: FirstNode()})
