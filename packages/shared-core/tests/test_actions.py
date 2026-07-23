from pydantic import TypeAdapter

import teyuna_shared


def test_player_action_union_round_trip() -> None:
    action = teyuna_shared.DiscardResourcesAction(
        by="alice",
        count={teyuna_shared.ResourceCard.MAIZE: 2},
    )
    dumped = action.model_dump(mode="json")
    assert dumped["kind"] == "discard_resources"
    parsed: teyuna_shared.AnyPlayerAction = TypeAdapter(
        teyuna_shared.AnyPlayerAction
    ).validate_python(dumped)
    assert isinstance(parsed, teyuna_shared.DiscardResourcesAction)
    assert parsed.count[teyuna_shared.ResourceCard.MAIZE] == 2


def test_action_result_preserves_nested_action_fields() -> None:
    action = teyuna_shared.MoveConquistatorAction(
        by="bob", q=1, r=0, from_player="carol"
    )
    result = teyuna_shared.MovedConquistatorResult(
        previous_phase=teyuna_shared.GamePhaseName.MOVE_CONQUISTATOR,
        next_phase=teyuna_shared.GamePhaseName.TRADE_AND_BUILD,
        action=action,
        q=1,
        r=0,
        from_player="carol",
    )
    dumped = result.model_dump(mode="json")
    assert dumped["kind"] == "moved_conquistator"
    assert dumped["action"]["kind"] == "move_conquistator"
    assert dumped["action"]["q"] == 1
    assert dumped["action"]["from_player"] == "carol"

    parsed: teyuna_shared.AnyActionExecutionResult = TypeAdapter(
        teyuna_shared.AnyActionExecutionResult
    ).validate_python(dumped)
    assert isinstance(parsed, teyuna_shared.MovedConquistatorResult)
    assert isinstance(parsed.action, teyuna_shared.MoveConquistatorAction)
    assert parsed.action.q == 1
