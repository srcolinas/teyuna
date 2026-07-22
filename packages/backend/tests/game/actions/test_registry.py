import datetime
from typing import Any, cast

import pytest

from src.game import actions, entities


def test_registered_handler_can_be_executed(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction.model_construct(by="player")

    def handle_dummy(
        game: entities.Game, action: DummyAction
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=entities.GamePhaseName.DICE_ROLL,
            action=action,
        )

    registry.register(entities.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    result = registry.execute(game, action)

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.DICE_ROLL


def test_unregistered_phase_raises(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    action = DummyAction.model_construct(by="player")

    game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    with pytest.raises(
        actions.GamePhaseHanlderNotImplementedError,
        match="No handlers defined for game phase: first placement",
    ):
        registry.execute(game, action)


def test_unregistered_action_type_raises(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()

    def handle_dummy(
        game: entities.Game, action: DummyAction
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            previous_phase=game.phase,
            next_phase=entities.GamePhaseName.DICE_ROLL,
            action=action,
        )

    registry.register(entities.GamePhaseName.FIRST_PLACEMENT)(handle_dummy)

    game.phase = entities.GamePhaseName.FIRST_PLACEMENT
    with pytest.raises(
        actions.ActionNotAllowedError,
        match="Action 'OtherAction' by 'player' is not allowed during the 'first placement' phase.",
    ):
        registry.execute(game, OtherAction.model_construct(by="player"))


def test_end_game_handler_keeps_phase(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.END_GAME)(actions.handle_end_game)

    game.phase = entities.GamePhaseName.END_GAME
    result = registry.execute(
        game,
        actions.PlayerAction.model_construct(by="player"),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.END_GAME


def test_end_game_rejects_unregistered_action_types(game: entities.Game) -> None:
    registry = actions.ActionsRegistry()
    registry.register(entities.GamePhaseName.END_GAME)(actions.handle_end_game)

    game.phase = entities.GamePhaseName.END_GAME
    with pytest.raises(actions.ActionNotAllowedError):
        registry.execute(
            game,
            DummyAction.model_construct(by="player"),
        )


def test_register_requires_at_least_two_parameters() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(game: entities.Game) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            previous_phase=entities.GamePhaseName.DICE_ROLL,
            next_phase=entities.GamePhaseName.DICE_ROLL,
            action=actions.PlayerAction.model_construct(by="player"),
        )

    with pytest.raises(ValueError, match="must accept at least two parameters"):
        registry.register(entities.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
        )


def test_register_requires_player_action_annotation() -> None:
    registry = actions.ActionsRegistry()

    def handle_invalid(
        game: entities.Game, action: str
    ) -> actions.ActionExecutionResult:
        return actions.ActionExecutionResult(
            previous_phase=entities.GamePhaseName.DICE_ROLL,
            next_phase=entities.GamePhaseName.DICE_ROLL,
            action=actions.PlayerAction.model_construct(by="player"),
        )

    with pytest.raises(TypeError, match="must be annotated with a subclass"):
        registry.register(entities.GamePhaseName.FIRST_PLACEMENT)(
            cast(Any, handle_invalid)
        )


class DummyAction(actions.PlayerAction):
    pass


class OtherAction(actions.PlayerAction):
    pass


@pytest.fixture
def game() -> entities.Game:
    mountains = entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=1)
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=entities.HexLocation(q=0, r=0),
        players={"player": entities.Player()},
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_
