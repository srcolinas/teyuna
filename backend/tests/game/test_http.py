import pytest
from fastapi import status

from src.game import actions, entities, http as http_module


def test_raise_if_failed_raises_400_with_error_detail() -> None:
    action = actions.PlayerAction.model_construct(by="player")
    result = actions.ActionExecutionResult(
        previous_phase=entities.GamePhaseName.LOBBY,
        next_phase=entities.GamePhaseName.LOBBY,
        action=action,
        error="not your turn",
    )

    with pytest.raises(Exception) as exc_info:
        http_module.raise_if_failed(result)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]
    assert exc_info.value.detail == "not your turn"  # type: ignore[attr-defined]


def test_raise_if_failed_does_nothing_when_no_error() -> None:
    action = actions.PlayerAction.model_construct(by="player")
    result = actions.ActionExecutionResult(
        previous_phase=entities.GamePhaseName.LOBBY,
        next_phase=entities.GamePhaseName.LOBBY,
        action=action,
    )

    http_module.raise_if_failed(result)
