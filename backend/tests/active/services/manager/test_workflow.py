import pytest
import uuid

from src.active import entities, services


def test_cannot_run_game_that_does_not_exist():
    manager = services.GameManager({})
    with pytest.raises(services.ActiveGameDoesNotExistError):
        manager.run(
            uuid.uuid4(),
            services.PlayerRequest(by="player1", action=services.AdvancePhaseAction()),
        )


def test_runs_player_request_through_nodes():
    class SuperFakeError(Exception): ...

    class FakeNode(services.GamePhaseNode):
        def run(
            self, game: entities.ActiveGame, request: services.PlayerRequest
        ) -> bool:
            raise SuperFakeError

        def on_exit(self, game: entities.ActiveGame) -> entities.GamePhaseName:
            return entities.GamePhaseName.FIRST_PLACEMENT

    manager = services.GameManager(
        {entities.GamePhaseName.FIRST_PLACEMENT: FakeNode()},
        start=entities.GamePhaseName.FIRST_PLACEMENT,
    )
    id = manager.create_game(["srcolinas-1", "srcolinas-2"])
    request = services.PlayerRequest(
        by="srcolinas-1", action=services.AdvancePhaseAction()
    )
    with pytest.raises(SuperFakeError):
        manager.run(id, request)


def test_advances_phase_if_run_triggers_termination():
    class SuperFakeError(Exception): ...

    class FirstNode(services.GamePhaseNode):
        def run(
            self, game: entities.ActiveGame, request: services.PlayerRequest
        ) -> bool:
            return True

        def on_exit(self, game: entities.ActiveGame) -> entities.GamePhaseName:
            return entities.GamePhaseName.SECOND_PLACEMENT

    class SecondNode(services.GamePhaseNode):
        def run(
            self, game: entities.ActiveGame, request: services.PlayerRequest
        ) -> bool:
            raise SuperFakeError

        def on_exit(self, game: entities.ActiveGame) -> entities.GamePhaseName:
            return entities.GamePhaseName.PRE_PRODUCTION

    manager = services.GameManager(
        {
            entities.GamePhaseName.FIRST_PLACEMENT: FirstNode(),
            entities.GamePhaseName.SECOND_PLACEMENT: SecondNode(),
        },
        start=entities.GamePhaseName.FIRST_PLACEMENT,
    )
    id = manager.create_game(["srcolinas-1", "srcolinas-2"])
    request = services.PlayerRequest(
        by="srcolinas-1", action=services.AdvancePhaseAction()
    )
    manager.run(id, request)
    with pytest.raises(SuperFakeError):
        manager.run(id, request)
