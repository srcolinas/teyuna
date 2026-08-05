import pytest
from pydantic import TypeAdapter

import teyuna_core


def test_action_events_round_trip_with_shared_unions() -> None:
    action = teyuna_core.MoveConquistatorAction(q=1, r=0, from_player="carol")
    result = teyuna_core.MovedConquistatorResult(
        previous_phase=teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        next_phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
        action=action,
        q=1,
        r=0,
        from_player="carol",
    )
    event = teyuna_core.SuccessfulActionEvent(
        by="alice",
        due_to_timeout=False,
        action=action,
        result=result,
    )

    dumped = event.model_dump(mode="json")
    assert dumped["type"] == "successful_action"
    assert dumped["action"]["kind"] == "move_conquistator"
    assert dumped["result"]["kind"] == "moved_conquistator"
    assert "rng" not in dumped

    parsed: teyuna_core.AnyGameEvent = TypeAdapter(
        teyuna_core.AnyGameEvent
    ).validate_python(dumped)
    assert isinstance(parsed, teyuna_core.SuccessfulActionEvent)
    assert isinstance(parsed.action, teyuna_core.MoveConquistatorAction)
    assert isinstance(parsed.result, teyuna_core.MovedConquistatorResult)


def test_failed_action_round_trips_with_typed_action() -> None:
    event = teyuna_core.FailedActionEvent(
        by="alice",
        due_to_timeout=True,
        action=teyuna_core.PlayerAction(),
        error="action is not valid in this phase",
    )

    parsed: teyuna_core.AnyGameEvent = TypeAdapter(
        teyuna_core.AnyGameEvent
    ).validate_json(event.model_dump_json())
    assert isinstance(parsed, teyuna_core.FailedActionEvent)
    assert isinstance(parsed.action, teyuna_core.PlayerAction)
    assert parsed.due_to_timeout is True


@pytest.mark.parametrize(
    ("event", "event_type"),
    [
        (teyuna_core.MessageEvent(by="alice", text="hello"), "message"),
        (
            teyuna_core.PhaseChangedEvent(
                previous_phase=teyuna_core.GamePhaseName.LOBBY,
                next_phase=teyuna_core.GamePhaseName.FIRST_PLACEMENT,
            ),
            "phase_changed",
        ),
        (
            teyuna_core.TurnChangedEvent(
                previous_player=None,
                next_player="alice",
            ),
            "turn_changed",
        ),
        (
            teyuna_core.BiggestArmyChangedEvent(
                previous_holder=None,
                current_holder="alice",
                previous_size=2,
                current_size=3,
            ),
            "biggest_army_changed",
        ),
        (
            teyuna_core.LongestRoadChangedEvent(
                previous_holder="alice",
                current_holder=None,
                previous_length=5,
                current_length=4,
            ),
            "longest_road_changed",
        ),
        (
            teyuna_core.EndGameEvent(winner=None, reason="game abandoned"),
            "end_game",
        ),
    ],
)
def test_game_event_union_uses_type_discriminant(
    event: teyuna_core.GameEventBase,
    event_type: str,
) -> None:
    dumped = event.model_dump(mode="json")
    parsed: teyuna_core.AnyGameEvent = TypeAdapter(
        teyuna_core.AnyGameEvent
    ).validate_python(dumped)

    assert dumped["type"] == event_type
    assert type(parsed) is type(event)
