from collections.abc import Callable, Coroutine
from typing import Any, Final

import fastapi
from fastapi import status
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from . import actions, repository as repository_module


class ActiveGameRoute(APIRoute):
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


def raise_if_failed(result: actions.ActionExecutionResult) -> None:
    if result.succeeded:
        return
    assert result.error is not None
    status_code = _STATUS_BY_EXCEPTION.get(type(result.error))
    if status_code is None:
        raise result.error
    raise fastapi.HTTPException(status_code=status_code, detail=str(result.error))


_STATUS_BY_EXCEPTION: Final[dict[type[BaseException], int]] = {
    repository_module.ActiveGameDoesNotExistError: status.HTTP_404_NOT_FOUND,
    actions.PlayerNotInTurnError: status.HTTP_403_FORBIDDEN,
    actions.GamePhaseHanlderNotImplementedError: status.HTTP_501_NOT_IMPLEMENTED,
    actions.ActionNotAllowedError: status.HTTP_400_BAD_REQUEST,
    actions.InvalidConquistatorLocation: status.HTTP_400_BAD_REQUEST,
    actions.InvalidSettlementLocation: status.HTTP_400_BAD_REQUEST,
    actions.InvalidPathLocation: status.HTTP_400_BAD_REQUEST,
    actions.PlayerDoesNotHaveCardError: status.HTTP_400_BAD_REQUEST,
    actions.InsufficientResourcesError: status.HTTP_400_BAD_REQUEST,
    actions.InsufficientResourceSupplyError: status.HTTP_400_BAD_REQUEST,
    actions.EmptyWisdomDeckError: status.HTTP_400_BAD_REQUEST,
    actions.InvalidTradeTargets: status.HTTP_400_BAD_REQUEST,
    actions.TradeProposalNotFound: status.HTTP_400_BAD_REQUEST,
    actions.TradeNotAddressedToPlayerError: status.HTTP_400_BAD_REQUEST,
    actions.PlayerNotRequiredToDiscardError: status.HTTP_400_BAD_REQUEST,
    actions.InvalidDiscardCountError: status.HTTP_400_BAD_REQUEST,
}
