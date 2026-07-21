import dataclasses
import datetime
import inspect
import random
from collections.abc import Callable
from typing import Any

import pydantic

from .. import player
from .. import entities


class ActionExecutionResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    succeeded: bool
    phase: entities.GamePhaseName
    by: player.Nickname
    due_to_timeout: bool = False
    error: Exception | None = None

    @pydantic.field_serializer("error")
    def _serialize_error(self, error: Exception | None) -> str | None:
        return type(error).__name__ if error is not None else None


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerAction:
    by: player.Nickname
    due_to_timeout: bool = dataclasses.field(default=False, kw_only=True)
    rng_: random.Random = dataclasses.field(default_factory=random.Random, kw_only=True)


TimeoutFn = Callable[[entities.Game, random.Random], PlayerAction]


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseTimeout:
    duration: datetime.timedelta
    on_timeout: TimeoutFn


class GamePhaseHanlderNotImplementedError(Exception):
    pass


class ActionNotAllowedError(Exception):
    pass


class ActionsRegistry:
    def __init__(self) -> None:
        self._registry: dict[
            entities.GamePhaseName,
            dict[
                type[PlayerAction],
                Callable[[entities.Game, Any], ActionExecutionResult],
            ],
        ] = {}
        self._timeouts: dict[entities.GamePhaseName, PhaseTimeout] = {}

    def register[ActionT: PlayerAction](
        self,
        phase: entities.GamePhaseName,
    ) -> Callable[
        [Callable[[entities.Game, ActionT], ActionExecutionResult]],
        Callable[[entities.Game, ActionT], ActionExecutionResult],
    ]:
        def decorator(
            handler: Callable[[entities.Game, ActionT], ActionExecutionResult],
        ) -> Callable[[entities.Game, ActionT], ActionExecutionResult]:
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
                action_type, PlayerAction
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
        phase: entities.GamePhaseName,
        duration: datetime.timedelta,
        on_timeout: TimeoutFn,
    ) -> None:
        self._timeouts[phase] = PhaseTimeout(duration=duration, on_timeout=on_timeout)

    def timeout_for(self, phase: entities.GamePhaseName) -> PhaseTimeout:
        try:
            return self._timeouts[phase]
        except KeyError:
            raise KeyError(
                f"No timeout defined for game phase: {phase.value}"
            ) from None

    def execute(
        self, game: entities.Game, action: PlayerAction
    ) -> ActionExecutionResult:
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
