import datetime
import random
from typing import Any, cast

import pytest

from src.game import actions, entities
import teyuna_core


def test_registered_handler_can_be_executed(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction()

    def handle_dummy(
        game: entities.Game,
        context: actions.ExecutionContext,
        action: DummyAction,
    ) -> teyuna_core.ActionExecutionResult:
        return teyuna_core.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            action=action,
        )

    registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    game.phase = teyuna_core.GamePhaseName.FIRST_PLACEMENT
    result = registry.execute(game, _context(), action)

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL


def test_unregistered_phase_raises(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction()

    game.phase = teyuna_core.GamePhaseName.FIRST_PLACEMENT
    with pytest.raises(
        actions.GamePhaseHanlderNotImplementedError,
        match="No handlers defined for game phase: first placement",
    ):
        registry.execute(game, _context(), action)


def test_unregistered_action_type_raises(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()

    def handle_dummy(
        game: entities.Game,
        context: actions.ExecutionContext,
        action: DummyAction,
    ) -> teyuna_core.ActionExecutionResult:
        return teyuna_core.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            action=action,
        )

    registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    game.phase = teyuna_core.GamePhaseName.FIRST_PLACEMENT
    with pytest.raises(
        actions.ActionNotAllowedError,
        match="Action 'OtherAction' by 'player' is not allowed during the 'first placement' phase.",
    ):
        registry.execute(game, _context(), OtherAction())


def test_end_game_handler_keeps_phase(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.END_GAME)(actions.handle_end_game)

    game.phase = teyuna_core.GamePhaseName.END_GAME
    result = registry.execute(
        game,
        _context(),
        teyuna_core.PlayerAction(),
    )

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME


def test_end_game_rejects_unregistered_action_types(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(teyuna_core.GamePhaseName.END_GAME)(actions.handle_end_game)

    game.phase = teyuna_core.GamePhaseName.END_GAME
    with pytest.raises(actions.ActionNotAllowedError):
        registry.execute(
            game,
            _context(),
            DummyAction(),
        )


def test_register_requires_at_least_three_parameters() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(game: entities.Game) -> teyuna_core.ActionExecutionResult:
        return teyuna_core.ActionExecutionResult(
            previous_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            next_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            action=teyuna_core.PlayerAction(),
        )

    with pytest.raises(ValueError, match="must accept at least three parameters"):
        registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
        )


def test_register_requires_player_action_annotation() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(
        game: entities.Game,
        context: actions.ExecutionContext,
        action: str,
    ) -> teyuna_core.ActionExecutionResult:
        return teyuna_core.ActionExecutionResult(
            previous_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            next_phase=teyuna_core.GamePhaseName.DICE_ROLL,
            action=teyuna_core.PlayerAction(),
        )

    with pytest.raises(TypeError, match="must be annotated with a subclass"):
        registry.register(teyuna_core.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
        )


class DummyAction(teyuna_core.PlayerAction):
    pass


class OtherAction(teyuna_core.PlayerAction):
    pass


def _context() -> actions.ExecutionContext:
    return actions.ExecutionContext(
        by="player",
        due_to_timeout=False,
        rng=random.Random(0),
    )


@pytest.fixture
def game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        players={"player": entities.Player()},
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_
