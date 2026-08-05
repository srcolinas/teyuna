from pydantic import TypeAdapter

import teyuna_core

_SERVER_OWNED = frozenset({"by", "due_to_timeout", "rng_"})


def test_player_action_union_round_trip() -> None:
    action = teyuna_core.DiscardResourcesAction(
        count={teyuna_core.ResourceCard.MAIZE: 2},
    )
    dumped = action.model_dump(mode="json")
    assert dumped["kind"] == "discard_resources"
    parsed: teyuna_core.AnyPlayerAction = TypeAdapter(
        teyuna_core.AnyPlayerAction
    ).validate_python(dumped)
    assert isinstance(parsed, teyuna_core.DiscardResourcesAction)
    assert parsed.count[teyuna_core.ResourceCard.MAIZE] == 2


def test_server_owned_fields_omitted_from_json_schema() -> None:
    props = teyuna_core.PlayerAction.model_json_schema().get("properties", {})
    assert _SERVER_OWNED.isdisjoint(props)

    free_props = teyuna_core.FreePlacementAction.model_json_schema().get(
        "properties", {}
    )
    assert _SERVER_OWNED.isdisjoint(free_props)


def test_execution_fields_are_not_action_fields() -> None:
    action = teyuna_core.PlayerAction()
    dumped = action.model_dump(mode="json")
    assert _SERVER_OWNED.isdisjoint(dumped)


def test_action_result_preserves_nested_action_fields() -> None:
    action = teyuna_core.MoveConquistatorAction(q=1, r=0, from_player="carol")
    result = teyuna_core.MovedConquistatorResult(
        previous_phase=teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        next_phase=teyuna_core.GamePhaseName.TRADE_AND_BUILD,
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
    assert _SERVER_OWNED.isdisjoint(dumped["action"])

    parsed: teyuna_core.AnyActionExecutionResult = TypeAdapter(
        teyuna_core.AnyActionExecutionResult
    ).validate_python(dumped)
    assert isinstance(parsed, teyuna_core.MovedConquistatorResult)
    assert isinstance(parsed.action, teyuna_core.MoveConquistatorAction)
    assert parsed.action.q == 1
