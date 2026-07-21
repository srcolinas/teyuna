import pytest

from src.game import actions, entities, http as http_module


class _CustomError(Exception):
    pass


def test_raise_if_failed_reraises_unmapped_error() -> None:
    result = actions.ActionExecutionResult(
        succeeded=False,
        phase=entities.GamePhaseName.LOBBY,
        by="player",
        error=_CustomError("boom"),
    )

    with pytest.raises(_CustomError):
        http_module.raise_if_failed(result)


def test_raise_if_failed_maps_known_error_to_http_exception() -> None:
    result = actions.ActionExecutionResult(
        succeeded=False,
        phase=entities.GamePhaseName.LOBBY,
        by="player",
        error=actions.PlayerNotInTurnError("not your turn"),
    )

    with pytest.raises(Exception) as exc_info:
        http_module.raise_if_failed(result)
    assert exc_info.value.status_code == 403  # type: ignore[attr-defined]


def test_raise_if_failed_does_nothing_when_succeeded() -> None:
    result = actions.ActionExecutionResult(
        succeeded=True,
        phase=entities.GamePhaseName.LOBBY,
        by="player",
    )

    http_module.raise_if_failed(result)
