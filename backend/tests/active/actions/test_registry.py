import dataclasses
from typing import Any, cast

import pytest

from src.active import actions, entities


def test_registered_handler_can_be_executed(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction(by="player")

    def handle_dummy(
        game: entities.ActiveGame, action: DummyAction
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            succeeded=True,
            phase=actions.GamePhaseName.DICE_ROLL,
        )

    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    result = registry.execute(actions.GamePhaseName.FIRST_PLACEMENT, game, action)

    assert result.succeeded is True
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.error is None


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
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            succeeded=True,
            phase=actions.GamePhaseName.DICE_ROLL,
        )

    registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    with pytest.raises(
        actions.ActionNotAllowedError,
        match="Action 'OtherAction' by 'player' is not allowed during the 'first placement' phase.",
    ):
        registry.execute(
            actions.GamePhaseName.FIRST_PLACEMENT, game, OtherAction(by="player")
        )


def test_end_game_handler_keeps_phase(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.END_GAME)(actions.handle_end_game)

    result = registry.execute(
        actions.GamePhaseName.END_GAME,
        game,
        actions.PlayerAction(by="player"),
    )

    assert result.succeeded is True
    assert result.phase is actions.GamePhaseName.END_GAME
    assert result.error is None


def test_end_game_rejects_unregistered_action_types(game: entities.ActiveGame) -> None:
    registry = actions.ActionsRegistry()
    registry.register(actions.GamePhaseName.END_GAME)(actions.handle_end_game)

    with pytest.raises(actions.ActionNotAllowedError):
        registry.execute(
            actions.GamePhaseName.END_GAME,
            game,
            DummyAction(by="player"),
        )


def test_register_requires_at_least_two_parameters() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(game: entities.ActiveGame) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            succeeded=True,
            phase=actions.GamePhaseName.DICE_ROLL,
        )

    with pytest.raises(ValueError, match="must accept at least two parameters"):
        registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
        )


def test_register_requires_player_action_annotation() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(
        game: entities.ActiveGame, action: str
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            succeeded=True,
            phase=actions.GamePhaseName.DICE_ROLL,
        )

    with pytest.raises(TypeError, match="must be annotated with a subclass"):
        registry.register(actions.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
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
