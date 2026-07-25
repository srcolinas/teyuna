import dataclasses
import datetime
import inspect
import random
from collections.abc import Callable
from typing import Any

import teyuna_core

from .. import entities

TimeoutFn = Callable[[entities.Game, random.Random], teyuna_core.PlayerActionBase]


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseTimeout:
    duration: datetime.timedelta
    on_timeout: TimeoutFn


class GamePhaseHanlderNotImplementedError(Exception):
    pass


class ActionNotAllowedError(Exception):
    def __init__(
        self, message: str = "Action is not allowed in the current phase"
    ) -> None:
        super().__init__(message)


class ActionsRegistry:
    def __init__(self) -> None:
        self._registry: dict[
            teyuna_core.GamePhaseName,
            dict[
                type[teyuna_core.PlayerActionBase],
                Callable[[entities.Game, Any], teyuna_core.AnyActionExecutionResult],
            ],
        ] = {}
        self._timeouts: dict[teyuna_core.GamePhaseName, PhaseTimeout] = {}

    def register[ActionT: teyuna_core.PlayerActionBase](
        self,
        phase: teyuna_core.GamePhaseName,
    ) -> Callable[
        [Callable[[entities.Game, ActionT], teyuna_core.AnyActionExecutionResult]],
        Callable[[entities.Game, ActionT], teyuna_core.AnyActionExecutionResult],
    ]:
        def decorator(
            handler: Callable[
                [entities.Game, ActionT], teyuna_core.AnyActionExecutionResult
            ],
        ) -> Callable[[entities.Game, ActionT], teyuna_core.AnyActionExecutionResult]:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            if len(params) < 2:
                raise ValueError(
                    f"Handler '{handler.__name__}' must accept at least two parameters: (game, action)."
                )

            action_param_name = params[1].name

            annotations = inspect.get_annotations(handler)
            action_type = annotations.get(action_param_name)

            if not isinstance(action_type, type) or not issubclass(
                action_type, teyuna_core.PlayerActionBase
            ):
                raise TypeError(
                    f"The second parameter '{action_param_name}' of handler '{handler.__name__}' "
                    f"must be annotated with a subclass of PlayerActionBase (got {action_type})."
                )

            if phase not in self._registry:
                self._registry[phase] = {}

            self._registry[phase][action_type] = handler

            return handler

        return decorator

    def set_timeout(
        self,
        phase: teyuna_core.GamePhaseName,
        duration: datetime.timedelta,
        on_timeout: TimeoutFn,
    ) -> None:
        self._timeouts[phase] = PhaseTimeout(duration=duration, on_timeout=on_timeout)

    def timeout_for(self, phase: teyuna_core.GamePhaseName) -> PhaseTimeout:
        try:
            return self._timeouts[phase]
        except KeyError:
            raise KeyError(
                f"No timeout defined for game phase: {phase.value}"
            ) from None

    def execute(
        self, game: entities.Game, action: teyuna_core.PlayerActionBase
    ) -> teyuna_core.AnyActionExecutionResult:
        phase_handlers = self._registry.get(game.phase)
        if not phase_handlers:
            raise GamePhaseHanlderNotImplementedError(
                f"No handlers defined for game phase: {game.phase.value}"
            )

        action_type = type(action)
        handler = phase_handlers.get(action_type)

        if not handler:
            raise ActionNotAllowedError(
                f"Action '{action_type.__name__}' by '{action.by}' is not allowed "
                f"during the '{game.phase.value}' phase."
            )

        result = handler(game, action)
        return result
