import pytest
from fastapi import status

from src.game import http as http_module
import teyuna_core


def test_raise_if_failed_raises_400_with_error_detail() -> None:
    action = teyuna_core.PlayerAction.model_construct(by="player")
    result = teyuna_core.ActionExecutionResult(
        previous_phase=teyuna_core.GamePhaseName.LOBBY,
        next_phase=teyuna_core.GamePhaseName.LOBBY,
        action=action,
        error="not your turn",
    )

    with pytest.raises(Exception) as exc_info:
        http_module.raise_if_failed(result)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST  # type: ignore[attr-defined]
    assert exc_info.value.detail == "not your turn"  # type: ignore[attr-defined]


def test_raise_if_failed_does_nothing_when_no_error() -> None:
    action = teyuna_core.PlayerAction.model_construct(by="player")
    result = teyuna_core.ActionExecutionResult(
        previous_phase=teyuna_core.GamePhaseName.LOBBY,
        next_phase=teyuna_core.GamePhaseName.LOBBY,
        action=action,
    )

    http_module.raise_if_failed(result)
