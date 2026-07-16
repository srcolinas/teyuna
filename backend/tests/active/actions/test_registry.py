import dataclasses

import pytest

from src.active import actions, entities


def test_registered_handler_can_be_executed(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction(by="player")

    def handle_dummy(
        game: entities.ActiveGame, action: DummyAction
    ) -> actions.GamePhaseName:
        return actions.GamePhaseName.END

    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    result = registry.execute(actions.GamePhaseName.FIRST_PLACEMENT, game, action)

    assert result is actions.GamePhaseName.END


def test_unregistered_phase_raises(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction(by="player")

    with pytest.raises(
        actions.GamePhaseHanlderNotImplementedError,
        match="No handlers defined for game phase: first placement",
    ):
        registry.execute(actions.GamePhaseName.FIRST_PLACEMENT, game, action)


def test_unregistered_action_type_raises(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()

    def handle_dummy(
        game: entities.ActiveGame, action: DummyAction
    ) -> actions.GamePhaseName:
        return actions.GamePhaseName.END

    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    with pytest.raises(
        actions.ActionNotAllowedError,
        match="Action 'OtherAction' is not allowed during the 'first placement' phase.",
    ):
        registry.execute(
            actions.GamePhaseName.FIRST_PLACEMENT, game, OtherAction(by="player")
        )


@dataclasses.dataclass(frozen=True, slots=True)
class DummyAction(actions.PlayerAction):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class OtherAction(actions.PlayerAction):
    pass


@pytest.fixture
def game() -> entities.ActiveGame:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    return entities.ActiveGame(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=0, r=0),
        turn_order=("player",),
        players={"player": entities.Player()},
    )
