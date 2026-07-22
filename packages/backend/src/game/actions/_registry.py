import dataclasses
import datetime
import inspect
import random
from collections.abc import Callable
from typing import Any

import teyuna_shared

from .. import entities

TimeoutFn = Callable[[entities.Game, random.Random], teyuna_shared.PlayerAction]


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
            teyuna_shared.GamePhaseName,
            dict[
                type[teyuna_shared.PlayerAction],
                Callable[[entities.Game, Any], teyuna_shared.ActionExecutionResult],
            ],
        ] = {}
        self._timeouts: dict[teyuna_shared.GamePhaseName, PhaseTimeout] = {}

    def register[ActionT: teyuna_shared.PlayerAction](
        self,
        phase: teyuna_shared.GamePhaseName,
    ) -> Callable[
        [Callable[[entities.Game, ActionT], teyuna_shared.ActionExecutionResult]],
        Callable[[entities.Game, ActionT], teyuna_shared.ActionExecutionResult],
    ]:
        def decorator(
            handler: Callable[
                [entities.Game, ActionT], teyuna_shared.ActionExecutionResult
            ],
        ) -> Callable[[entities.Game, ActionT], teyuna_shared.ActionExecutionResult]:
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
                action_type, teyuna_shared.PlayerAction
            ):
                raise TypeError(
                    f"The second parameter '{action_param_name}' of handler '{handler.__name__}' "
                    f"must be annotated with a subclass of PlayerAction (got {action_type})."
                )

            if phase not in self._registry:
                self._registry[phase] = {}

            self._registry[phase][action_type] = handler

            return handler

        return decorator

    def set_timeout(
        self,
        phase: teyuna_shared.GamePhaseName,
        duration: datetime.timedelta,
        on_timeout: TimeoutFn,
    ) -> None:
        self._timeouts[phase] = PhaseTimeout(duration=duration, on_timeout=on_timeout)

    def timeout_for(self, phase: teyuna_shared.GamePhaseName) -> PhaseTimeout:
        try:
            return self._timeouts[phase]
        except KeyError:
            raise KeyError(
                f"No timeout defined for game phase: {phase.value}"
            ) from None

    def execute(
        self, game: entities.Game, action: teyuna_shared.PlayerAction
    ) -> teyuna_shared.ActionExecutionResult:
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
