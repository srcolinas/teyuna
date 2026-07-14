import pytest
import uuid

from src.active import entities, services
from src.active.services import phases


def test_cannot_run_game_that_does_not_exist():
    manager = services.GameManager({})
    with pytest.raises(services.ActiveGameDoesNotExistError):
        manager.run(
            uuid.uuid4(),
            phases.PlayerRequest(by="player1", action=phases.AdvancePhaseAction()),
        )


def test_runs_player_request_through_nodes():
    class SuperFakeError(Exception): ...

    class FakeNode(phases.GamePhaseNode[None, None, None]):
        def run(
            self, game: entities.ActiveGame, request: phases.PlayerRequest
        ) -> phases.RunOutcome[None]:
            raise SuperFakeError

        def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
            return phases.ExitOutcome(
                next=phases.GamePhaseName.FIRST_PLACEMENT, value=None
            )

        def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
            return phases.EnterOutcome(value=None)

    manager = services.GameManager(
        {phases.GamePhaseName.FIRST_PLACEMENT: FakeNode()},
        start=phases.GamePhaseName.FIRST_PLACEMENT,
    )
    id = manager.create_game(["srcolinas-1", "srcolinas-2"])
    request = phases.PlayerRequest(by="srcolinas-1", action=phases.AdvancePhaseAction())
    with pytest.raises(SuperFakeError):
        manager.run(id, request)


def test_advances_phase_if_run_triggers_termination():
    class SuperFakeError(Exception): ...

    class FirstNode(phases.GamePhaseNode[None, None, None]):
        def run(
            self, game: entities.ActiveGame, request: phases.PlayerRequest
        ) -> phases.RunOutcome[None]:
            return phases.RunOutcome(finished=True, value=None)

        def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
            return phases.ExitOutcome(
                next=phases.GamePhaseName.SECOND_PLACEMENT, value=None
            )

        def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
            return phases.EnterOutcome(value=None)

    class SecondNode(phases.GamePhaseNode[None, None, None]):
        def run(
            self, game: entities.ActiveGame, request: phases.PlayerRequest
        ) -> phases.RunOutcome[None]:
            raise SuperFakeError

        def on_exit(self, game: entities.ActiveGame) -> phases.ExitOutcome[None]:
            return phases.ExitOutcome(
                next=phases.GamePhaseName.PRE_DICE_ROLL, value=None
            )

        def on_enter(self, game: entities.ActiveGame) -> phases.EnterOutcome[None]:
            return phases.EnterOutcome(value=None)

    manager = services.GameManager(
        {
            phases.GamePhaseName.FIRST_PLACEMENT: FirstNode(),
            phases.GamePhaseName.SECOND_PLACEMENT: SecondNode(),
        },
        start=phases.GamePhaseName.FIRST_PLACEMENT,
    )
    id = manager.create_game(["srcolinas-1", "srcolinas-2"])
    request = phases.PlayerRequest(by="srcolinas-1", action=phases.AdvancePhaseAction())
    manager.run(id, request)
    with pytest.raises(SuperFakeError):
        manager.run(id, request)
