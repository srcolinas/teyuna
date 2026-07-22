from collections.abc import Callable, Coroutine
from typing import Any, Final

import fastapi
from fastapi import status
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

import teyuna_shared

from . import actions, entities, repository as repository_module, services


class GameRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            try:
                return await original(request)
            except Exception as exc:
                status_code = _STATUS_BY_EXCEPTION.get(type(exc))
                if status_code is None:
                    raise
                if status_code == status.HTTP_404_NOT_FOUND:
                    raise fastapi.HTTPException(status_code=status_code) from exc
                raise fastapi.HTTPException(
                    status_code=status_code, detail=str(exc)
                ) from exc

        return handler


def raise_if_failed(result: teyuna_shared.ActionExecutionResult) -> None:
    if result.error is None:
        return
    raise fastapi.HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.error,
    )


_STATUS_BY_EXCEPTION: Final[dict[type[BaseException], int]] = {
    repository_module.GameDoesNotExistError: status.HTTP_404_NOT_FOUND,
    services.GameAlreadyStartedError: status.HTTP_400_BAD_REQUEST,
    entities.GameAlreadyFullError: status.HTTP_400_BAD_REQUEST,
    entities.NicknameAlreadyTakenError: status.HTTP_400_BAD_REQUEST,
    actions.GamePhaseHanlderNotImplementedError: status.HTTP_501_NOT_IMPLEMENTED,
    actions.ActionNotAllowedError: status.HTTP_400_BAD_REQUEST,
}
